from app import app, db
from sqlalchemy import text
from datetime import datetime

def run_migrations():
    with app.app_context():
        # Vérifier si les colonnes existent déjà
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Créer une table temporaire avec la nouvelle structure
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS user_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                is_doctor BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0,
                doctor_status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP
            )
        '''))
        
        # Copier les données existantes
        db.session.execute(text('''
            INSERT INTO user_temp (id, username, email, password_hash, is_doctor, is_admin, doctor_status, created_at)
            SELECT id, username, email, password_hash, is_doctor, is_admin, 
                   CASE WHEN is_doctor = 1 THEN 'approved' ELSE 'pending' END,
                   datetime('now')
            FROM user
        '''))
        
        # Supprimer l'ancienne table
        db.session.execute(text('DROP TABLE user'))
        
        # Renommer la nouvelle table
        db.session.execute(text('ALTER TABLE user_temp RENAME TO user'))
        
        db.session.commit()
        print("Migration terminée avec succès")

if __name__ == '__main__':
    run_migrations() 