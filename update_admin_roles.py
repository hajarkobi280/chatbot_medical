from app import app, db, User

def update_admin_roles():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('Aucun utilisateur admin trouvé.')
            return
        admin.is_admin = True
        admin.is_doctor = False
        db.session.commit()
        print('Rôles admin mis à jour !')

if __name__ == '__main__':
    update_admin_roles() 