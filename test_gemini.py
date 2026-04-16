from chatbot_logic import MedicalChatbot
import os
from dotenv import load_dotenv

def test_gemini():
    # Chargement des variables d'environnement
    load_dotenv()
    
    # Vérification de la clé API
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Erreur: GOOGLE_API_KEY n'est pas définie dans le fichier .env")
        return
    
    # Initialisation du chatbot
    chatbot = MedicalChatbot()
    
    # Tests de différentes situations
    test_cases = [
        {
            "description": "Test d'une question générale",
            "input": "Bonjour, j'ai mal à la tête depuis hier",
            "is_doctor": False
        },
        {
            "description": "Test d'une urgence",
            "input": "J'ai une douleur thoracique intense et je respire difficilement",
            "is_doctor": False
        },
        {
            "description": "Test d'une question sur un médicament",
            "input": "Quels sont les effets secondaires du paracétamol ?",
            "is_doctor": False
        },
        {
            "description": "Test en mode médecin",
            "input": "Patient avec fièvre à 39°C et toux sèche depuis 3 jours",
            "is_doctor": True
        }
    ]
    
    # Exécution des tests
    print("\n=== Tests du Chatbot Médical avec Gemini ===\n")
    
    for test in test_cases:
        print(f"\n📝 Test: {test['description']}")
        print(f"Question: {test['input']}")
        print("\nRéponse:")
        try:
            response = chatbot.generate_response(test['input'], test['is_doctor'])
            print(response)
            print("\n" + "="*50)
        except Exception as e:
            print(f"❌ Erreur lors du test: {str(e)}")
            print("\n" + "="*50)

if __name__ == "__main__":
    test_gemini() 