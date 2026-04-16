from app import app, db, User

def update_admin_status():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('Aucun utilisateur admin trouvé.')
            return
        admin.doctor_status = 'approved'
        db.session.commit()
        print('Statut admin mis à jour !')

if __name__ == '__main__':
    update_admin_status() 