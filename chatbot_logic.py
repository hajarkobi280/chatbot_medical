import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import current_app
import logging
from typing import List, Dict, Optional
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import threading
import hashlib
from functools import lru_cache

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    """Exception raised when API quota is exceeded."""
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=2, reset_timeout=600):  # Increased timeout to 10 minutes
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3  # Reduced from 5 to 3
        self.backoff_factor = 2

    def record_failure(self):
        with self.lock:
            self.failures += 1
            self.consecutive_failures += 1
            self.last_failure_time = datetime.now()
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.warning(f"Trop d'échecs consécutifs ({self.consecutive_failures}). Augmentation du délai d'attente.")
                self.reset_timeout = min(self.reset_timeout * self.backoff_factor, 3600)  # Max 1 heure
                self.backoff_factor *= 2  # Exponential backoff

    def record_success(self):
        with self.lock:
            self.failures = 0
            self.consecutive_failures = 0
            self.last_failure_time = None
            self.reset_timeout = 600  # Reset to 10 minutes
            self.backoff_factor = 2  # Reset backoff factor

    def is_open(self):
        with self.lock:
            if self.failures >= self.failure_threshold:
                if self.last_failure_time:
                    time_since_last_failure = (datetime.now() - self.last_failure_time).total_seconds()
                    if time_since_last_failure < self.reset_timeout:
                        return True
                    else:
                        # Reset after timeout
                        self.failures = 0
                        self.consecutive_failures = 0
                        self.last_failure_time = None
                        self.backoff_factor = 2
            return False

class RateLimiter:
    def __init__(self, max_requests_per_minute=3):  # Reduced from 5 to 3
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
        self.circuit_breaker = CircuitBreaker()
        self.last_request_time = None
        self.min_request_interval = 20  # Increased from 12 to 20 seconds
        self.request_count = 0
        self.daily_limit = 100  # Daily request limit
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def _reset_daily_counter(self):
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.request_count = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def wait_if_needed(self):
        with self.lock:
            self._reset_daily_counter()
            
            if self.request_count >= self.daily_limit:
                wait_time = (self.daily_reset_time + timedelta(days=1) - datetime.now()).total_seconds()
                logger.warning(f"Limite quotidienne atteinte. Attente de {wait_time:.0f} secondes jusqu'à la réinitialisation.")
                time.sleep(wait_time)
                self.request_count = 0
                return

            if self.circuit_breaker.is_open():
                wait_time = self.circuit_breaker.reset_timeout
                logger.warning(f"Circuit breaker is open. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return

            now = datetime.now()
            
            # Enforce minimum interval between requests
            if self.last_request_time:
                time_since_last_request = (now - self.last_request_time).total_seconds()
                if time_since_last_request < self.min_request_interval:
                    wait_time = self.min_request_interval - time_since_last_request
                    logger.info(f"Respecting minimum interval. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    now = datetime.now()

            # Remove requests older than 1 minute
            self.requests = [req for req in self.requests if now - req < timedelta(minutes=1)]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time until oldest request is 1 minute old
                wait_time = 60 - (now - self.requests[0]).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    now = datetime.now()
            
            self.requests.append(now)
            self.last_request_time = now
            self.request_count += 1

class MedicalChatbot:
    def __init__(self):
        """Initialise le chatbot médical avec Gemini."""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("La clé API Google n'est pas configurée")
        
        # Configuration de l'API Gemini
        genai.configure(
            api_key=self.api_key,
            transport='rest'
        )
        
        # Initialiser le rate limiter avec un circuit breaker
        self.rate_limiter = RateLimiter(max_requests_per_minute=3)
        
        # Cache pour les réponses fréquentes
        self.response_cache = {}
        self.cache_ttl = 3600  # 1 heure
        
        # Vérifier les modèles disponibles
        try:
            # Afficher la version de l'API
            logger.info(f"Version de l'API Google Generative AI: {genai.__version__}")
            
            # Lister tous les modèles disponibles
            models = genai.list_models()
            logger.info("Modèles disponibles:")
            available_models = []
            for model in models:
                logger.info(f"- {model.name}")
                logger.info(f"  Méthodes supportées: {model.supported_generation_methods}")
                available_models.append(model.name)
            
            # Vérifier si gemini-1.5-flash est disponible
            model_name = 'models/gemini-1.5-flash'
            
            if model_name not in available_models:
                logger.error(f"Le modèle {model_name} n'est pas disponible.")
                logger.error(f"Modèles disponibles: {available_models}")
                raise ValueError(f"Le modèle {model_name} n'est pas disponible. Modèles disponibles: {available_models}")
            
            # Vérifier les méthodes supportées pour gemini-1.5-flash
            model_info = next((m for m in models if m.name == model_name), None)
            if model_info:
                logger.info(f"Méthodes supportées pour {model_name}: {model_info.supported_generation_methods}")
                if 'generateContent' not in model_info.supported_generation_methods:
                    raise ValueError(f"Le modèle {model_name} ne supporte pas la méthode generateContent")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des modèles: {str(e)}")
            raise
        
        # Initialisation du modèle avec les paramètres de sécurité
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                'temperature': 0.3,
                'top_p': 0.9,
                'top_k': 40,
                'max_output_tokens': 1000,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        self.conversation_history = []
        self.max_history_length = 10
        self.logger = logger

    def _is_emergency_context(self, text: str) -> bool:
        """Détecte un contexte urgent avec des mots-clés critiques."""
        emergency_keywords = [
            "étouffe", "saigne abondamment", "perte connaissance", 
            "brûlure grave", "crise convulsive", "douleur intense",
            "douleur thoracique", "difficulté respiratoire", "raq"
        ]
        return any(keyword in text.lower() for keyword in emergency_keywords)

    def _handle_api_error(self, error: Exception) -> str:
        """Gère les erreurs de l'API de manière appropriée."""
        error_str = str(error)
        
        if "429" in error_str and "quota" in error_str.lower():
            self.logger.warning("Quota API dépassé. Attente recommandée avant nouvelle tentative.")
            # Extract retry delay from error message if available
            retry_delay = 300  # Default to 5 minutes
            if "retry_delay" in error_str:
                try:
                    retry_delay = int(error_str.split("seconds")[0].split()[-1])
                except:
                    pass
            self.rate_limiter.circuit_breaker.record_failure()
            raise QuotaExceededError(f"Le quota d'utilisation de l'API a été dépassé. Veuillez réessayer dans {retry_delay} secondes.")
        
        if "timeout" in error_str.lower():
            self.logger.warning("Timeout lors de l'appel à l'API")
            raise TimeoutError("Le délai d'attente de l'API a été dépassé")
        
        self.logger.error(f"Erreur API non gérée: {error_str}")
        return "Désolé, une erreur est survenue lors de la communication avec l'API. Veuillez réessayer."

    @lru_cache(maxsize=100)
    def _get_cached_response(self, query_hash: str) -> Optional[str]:
        """Récupère une réponse du cache si elle existe et n'est pas expirée."""
        if query_hash in self.response_cache:
            timestamp, response = self.response_cache[query_hash]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return response
            else:
                del self.response_cache[query_hash]
        return None

    def _cache_response(self, query_hash: str, response: str):
        """Stocke une réponse dans le cache."""
        self.response_cache[query_hash] = (datetime.now(), response)

    def _generate_query_hash(self, user_input: str, is_doctor: bool) -> str:
        """Génère un hash unique pour la requête."""
        query_str = f"{user_input}:{is_doctor}"
        return hashlib.md5(query_str.encode()).hexdigest()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutError, QuotaExceededError)),
        reraise=True
    )
    def _generate_llm_response(self, user_input: str, is_doctor: bool = False) -> str:
        """Génère des réponses médicales avec Gemini."""
        try:
            # Check cache first
            query_hash = self._generate_query_hash(user_input, is_doctor)
            cached_response = self._get_cached_response(query_hash)
            if cached_response:
                logger.info("Réponse récupérée du cache")
                return cached_response

            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Construction du prompt
            prompt = f"""En tant qu'assistant médical expert francophone, répondez à la question suivante.
{'[MODE MÉDECIN]' if is_doctor else '[MODE PATIENT]'}

Question: {user_input}

Instructions:
1. Soyez professionnel et rassurant
2. Ne donnez pas de diagnostic définitif
3. Recommandez de consulter un médecin en cas de doute
4. Pour les urgences, commencez par ⚠️ URGENCE MÉDICALE
5. Structurez votre réponse de manière claire et concise"""

            # Génération de la réponse avec le SDK
            response = self.model.generate_content(prompt)
            
            # Vérification de la réponse
            if not response or not hasattr(response, 'text'):
                self.logger.error("Réponse invalide de l'API Gemini")
                return "Désolé, je n'ai pas pu générer une réponse valide. Veuillez réessayer."
            
            if response.prompt_feedback.block_reason:
                self.logger.warning(f"Contenu bloqué: {response.prompt_feedback.block_reason}")
                return "Désolé, je ne peux pas traiter cette demande pour des raisons de sécurité."
            
            # Vérification de la longueur de la réponse
            if len(response.text.strip()) < 10:
                self.logger.warning("Réponse trop courte de l'API Gemini")
                return "Désolé, la réponse générée n'est pas suffisamment détaillée. Veuillez reformuler votre question."
            
            # Cache the response
            self._cache_response(query_hash, response.text)
            return response.text

        except Exception as e:
            error_message = self._handle_api_error(e)
            self.logger.error(f"Erreur lors de la génération de la réponse: {str(e)}")
            return error_message

    def generate_response(self, user_input: str, is_doctor: bool = False) -> str:
        """Génère une réponse médicale adaptée."""
        try:
            # Vérification d'urgence immédiate
            if self._is_emergency_context(user_input):
                response = self._generate_llm_response(
                    f"⚠️ URGENCE DÉTECTÉE - {user_input}",
                    is_doctor
                )
            else:
                response = self._generate_llm_response(user_input, is_doctor)

            # Mise à jour de l'historique
            self._update_conversation_history(user_input, response)
            
            return response
            
        except QuotaExceededError as e:
            self.logger.error(f"Erreur de quota: {str(e)}")
            return str(e)  # Return the error message with retry delay
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {str(e)}")
            return "Désolé, une erreur inattendue est survenue. Veuillez réessayer plus tard."

    def _update_conversation_history(self, user_input: str, response: str):
        """Gère l'historique des conversations."""
        if len(self.conversation_history) >= self.max_history_length:
            self.conversation_history.pop(0)
        
        self.conversation_history.extend([
            {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
        ])

    def get_conversation_history(self) -> List[Dict]:
        """Retourne l'historique de la conversation."""
        return self.conversation_history