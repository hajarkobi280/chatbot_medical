from app import app, db, User
from werkzeug.security import generate_password_hash

def change_admin_password(new_password):
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('Aucun utilisateur admin trouvé.')
            return
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print('Mot de passe admin mis à jour !')

if __name__ == '__main__':
    new_password = input('Entrez le nouveau mot de passe : ')
    change_admin_password(new_password) 