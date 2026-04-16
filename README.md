# Chatbot Médical

Un chatbot médical intelligent qui aide les patients à comprendre leurs symptômes et guide les médecins dans leur pratique.

## Fonctionnalités

- Interface utilisateur moderne et responsive
- Détection automatique des symptômes
- Suggestions de spécialités médicales
- Détection des urgences
- Mode médecin avec outils spécialisés
- Historique des conversations
- Base de données des symptômes et spécialités

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Une clé API Google (Gemini)

## Installation

1. Cloner le dépôt :
```bash
git clone [URL_DU_REPO]
cd mon_chatbot_medical
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
   - Créer un fichier `.env` à la racine du projet
   - Copier le contenu suivant et remplacer les valeurs :
```
FLASK_APP=app.py
FLASK_ENV=development
FLASK_SECRET_KEY=votre-clé-secrète
DATABASE_URL=sqlite:///medical_chatbot.db
GOOGLE_API_KEY=votre-clé-api-google
HOST=0.0.0.0
PORT=5000
```

## Lancement

1. Initialiser la base de données :
```bash
flask db init
flask db migrate
flask db upgrade
```

2. Lancer l'application :
```bash
flask run
```

L'application sera accessible à l'adresse : http://localhost:5000

## Structure du Projet

```
mon_chatbot_medical/
├── app.py                 # Application principale Flask
├── chatbot_logic.py      # Logique du chatbot
├── requirements.txt      # Dépendances Python
├── static/              # Fichiers statiques
│   ├── css/            # Styles CSS
│   └── js/             # Scripts JavaScript
├── templates/           # Templates HTML
│   ├── login.html
│   ├── signup.html
│   ├── chat_user.html
│   ├── chat_doctor.html
│   └── doctordashboard.html
└── instance/           # Base de données SQLite
```

## Utilisation

1. Créer un compte utilisateur ou médecin
2. Se connecter avec vos identifiants
3. Commencer une conversation avec le chatbot
4. Pour les médecins, accéder aux outils spécialisés via le tableau de bord

## Sécurité

- Les mots de passe sont hachés avant stockage
- Les sessions sont sécurisées
- Les clés API sont stockées dans des variables d'environnement
- Protection contre les injections SQL

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 