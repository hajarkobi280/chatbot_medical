import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'environnement
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

if __name__ == '__main__':
    # Vérification des variables d'environnement critiques
    required_vars = ['FLASK_SECRET_KEY', 'GOOGLE_API_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Erreur : Variables d'environnement manquantes :")
        for var in missing_vars:
            print(f"- {var}")
        exit(1)
    
    print("Démarrage du serveur de production...")
    print("Utilisez la commande : gunicorn -c gunicorn_config.py app:app") 