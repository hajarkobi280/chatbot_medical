from app import app, db, User
from werkzeug.security import generate_password_hash
import os

def init_db():
    with app.app_context():
        # Supprimer la base de données existante
        db_path = os.path.join(app.instance_path, 'medical_chatbot.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Base de données existante supprimée.")
        
        # Créer toutes les tables
        db.create_all()
        print("Tables créées avec succès.")
        
        # Créer l'utilisateur admin
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            is_doctor=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Utilisateur admin créé avec succès!")
        print("Nom d'utilisateur: admin")
        print("Mot de passe: admin123")

if __name__ == '__main__':
    init_db() 