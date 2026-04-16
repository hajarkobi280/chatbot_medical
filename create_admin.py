from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Vérifier si l'admin existe déjà
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_doctor=True,
                doctor_status='approved'
            )
            db.session.add(admin)
            db.session.commit()
            print("Utilisateur administrateur créé avec succès")
        else:
            print("L'utilisateur administrateur existe déjà")

if __name__ == '__main__':
    create_admin_user() 