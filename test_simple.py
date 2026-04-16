import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger la clé API depuis le fichier .env
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("❌ Erreur: GOOGLE_API_KEY n'est pas définie dans le fichier .env")
    exit(1)

# Configurer l'API
genai.configure(api_key=api_key)

# Créer le modèle
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("\n✅ Modèle initialisé avec succès (gemini-1.5-flash)")
except Exception as e:
    print(f"\n❌ Erreur lors de l'initialisation du modèle: {str(e)}")
    exit(1)

# Tester avec une question simple
try:
    print("\n🔄 Envoi de la requête à Gemini...")
    response = model.generate_content("Dis-moi bonjour en français")
    print("\n✅ Réponse reçue de Gemini :")
    print(response.text)
except Exception as e:
    print(f"\n❌ Erreur lors de l'appel à l'API : {str(e)}")
    exit(1) 