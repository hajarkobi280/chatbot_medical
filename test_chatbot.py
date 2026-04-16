import unittest
from chatbot_logic import MedicalChatbot, QuotaExceededError
import os
from dotenv import load_dotenv
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMedicalChatbot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests."""
        load_dotenv()
        if not os.getenv('GOOGLE_API_KEY'):
            raise ValueError("GOOGLE_API_KEY non trouvée dans le fichier .env")
        cls.chatbot = MedicalChatbot()
        # Attendre plus longtemps pour éviter les problèmes de quota
        time.sleep(5)

    def setUp(self):
        """Configuration avant chaque test."""
        # Attendre entre chaque test pour respecter les limites de quota
        time.sleep(3)

    def test_initialization(self):
        """Test de l'initialisation du chatbot."""
        self.assertIsNotNone(self.chatbot)
        self.assertIsNotNone(self.chatbot.model)
        self.assertEqual(len(self.chatbot.conversation_history), 0)

    def test_emergency_detection(self):
        """Test de la détection des urgences."""
        emergency_cases = [
            "J'ai une douleur thoracique intense",
            "Je saigne abondamment",
            "Je respire difficilement",
            "J'ai une brûlure grave"
        ]
        
        non_emergency_cases = [
            "J'ai un petit rhume",
            "Je me sens fatigué",
            "J'ai mal à la tête"
        ]

        for case in emergency_cases:
            self.assertTrue(
                self.chatbot._is_emergency_context(case),
                f"Le cas d'urgence n'a pas été détecté: {case}"
            )

        for case in non_emergency_cases:
            self.assertFalse(
                self.chatbot._is_emergency_context(case),
                f"Faux positif pour l'urgence: {case}"
            )

    def test_basic_response(self):
        """Test des réponses basiques."""
        try:
            question = "Bonjour, j'ai mal à la tête"
            response = self.chatbot.generate_response(question)
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 10)
        except QuotaExceededError as e:
            logger.warning(f"Test ignoré - Quota dépassé: {str(e)}")
            self.skipTest("Quota API dépassé")

    def test_doctor_mode(self):
        """Test du mode médecin."""
        try:
            question = "Patient avec fièvre à 39°C et toux sèche"
            response = self.chatbot.generate_response(question, is_doctor=True)
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 10)
        except QuotaExceededError as e:
            logger.warning(f"Test ignoré - Quota dépassé: {str(e)}")
            self.skipTest("Quota API dépassé")

    def test_conversation_history(self):
        """Test de l'historique des conversations."""
        try:
            # Ajouter quelques messages
            self.chatbot.generate_response("Bonjour")
            time.sleep(2)  # Attendre entre les messages
            self.chatbot.generate_response("Comment allez-vous?")
            
            history = self.chatbot.get_conversation_history()
            self.assertEqual(len(history), 4)  # 2 paires de messages (user + bot)
            
            # Vérifier la structure des messages
            for message in history:
                self.assertIn('role', message)
                self.assertIn('content', message)
                self.assertIn('timestamp', message)
                self.assertIn(message['role'], ['user', 'assistant'])
        except QuotaExceededError as e:
            logger.warning(f"Test ignoré - Quota dépassé: {str(e)}")
            self.skipTest("Quota API dépassé")

    def test_error_handling(self):
        """Test de la gestion des erreurs."""
        try:
            # Test avec une question vide
            response = self.chatbot.generate_response("")
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)

            time.sleep(2)  # Attendre entre les tests

            # Test avec une question très longue
            long_question = "?" * 1000
            response = self.chatbot.generate_response(long_question)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)
        except QuotaExceededError as e:
            logger.warning(f"Test ignoré - Quota dépassé: {str(e)}")
            self.skipTest("Quota API dépassé")

def test_chatbot():
    try:
        # Initialiser le chatbot
        print("\n🔄 Initialisation du chatbot...")
        chatbot = MedicalChatbot()
        print("✅ Chatbot initialisé avec succès")

        # Test 1: Question simple
        print("\n🔄 Test 1: Question simple")
        question1 = "J'ai mal à la tête, que puis-je faire ?"
        print(f"Question: {question1}")
        response1 = chatbot.generate_response(question1)
        print(f"Réponse: {response1}")

        # Test 2: Question plus complexe
        print("\n🔄 Test 2: Question plus complexe")
        question2 = "Quels sont les symptômes de la grippe et comment la soigner ?"
        print(f"Question: {question2}")
        response2 = chatbot.generate_response(question2)
        print(f"Réponse: {response2}")

        # Test 3: Mode médecin
        print("\n🔄 Test 3: Mode médecin")
        question3 = "Quels sont les traitements recommandés pour une infection urinaire ?"
        print(f"Question (mode médecin): {question3}")
        response3 = chatbot.generate_response(question3, is_doctor=True)
        print(f"Réponse: {response3}")

    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        raise

if __name__ == "__main__":
    test_chatbot() 