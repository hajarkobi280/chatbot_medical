from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
import os
from datetime import datetime
from functools import wraps
from chatbot_logic import MedicalChatbot
from dotenv import load_dotenv
import json
import secrets
import re
from models import db, User, Chat, Message, Disease, Medicine

# Chargement des variables d'environnement
load_dotenv()

# Génération d'une clé secrète par défaut
DEFAULT_SECRET_KEY = secrets.token_hex(32)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', DEFAULT_SECRET_KEY)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///medical_chatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Si la clé secrète n'était pas dans le fichier .env, afficher un message
if not os.getenv('FLASK_SECRET_KEY'):
    print(f"Clé secrète générée : {DEFAULT_SECRET_KEY}")
    print("Veuillez ajouter cette clé à votre fichier .env comme FLASK_SECRET_KEY")

# Initialisation de la base de données
db.init_app(app)

# Configuration de l'API Google
google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    print("ATTENTION: GOOGLE_API_KEY n'est pas définie dans le fichier .env")
    print("Le chatbot ne pourra pas fonctionner sans une clé API Google valide")
genai.configure(api_key=google_api_key)

# Initialisation du chatbot
chatbot = MedicalChatbot()

# Constantes
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 8

# Décorateurs
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "error")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash("Accès non autorisé.", "error")
            return redirect(url_for('chat_user'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "error")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_doctor or user.doctor_status != 'approved':
            flash("Accès non autorisé.", "error")
            return redirect(url_for('chat_user'))
        return f(*args, **kwargs)
    return decorated_function

# Fonctions utilitaires
def validate_email(email):
    return bool(re.match(EMAIL_PATTERN, email))

def validate_username(username):
    return MIN_USERNAME_LENGTH <= len(username) <= MAX_USERNAME_LENGTH

def validate_password(password):
    return len(password) >= MIN_PASSWORD_LENGTH

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_doctor'] = user.is_doctor
            session['is_admin'] = user.is_admin
            
            if user.is_admin:
                return redirect(url_for('admin_interface'))
            if user.is_doctor:
                return redirect(url_for('doctor_dashboard'))
            return redirect(url_for('chat_user'))
            
        flash("Identifiants invalides. Veuillez vérifier votre nom d'utilisateur et votre mot de passe.", "error")
        return render_template('login.html')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            is_doctor = request.form.get('is_doctor') == 'on'
            
            # Validation des champs
            if not all([username, email, password, confirm_password]):
                flash("Tous les champs sont obligatoires", "error")
                return render_template('signup.html')
            
            if not validate_username(username):
                flash(f"Le nom d'utilisateur doit contenir entre {MIN_USERNAME_LENGTH} et {MAX_USERNAME_LENGTH} caractères", "error")
                return render_template('signup.html')
            
            if not validate_email(email):
                flash("Format d'email invalide", "error")
                return render_template('signup.html')
            
            if not validate_password(password):
                flash(f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères", "error")
                return render_template('signup.html')
            
            if password != confirm_password:
                flash("Les mots de passe ne correspondent pas", "error")
                return render_template('signup.html')
            
            # Vérification des doublons
            if User.query.filter_by(username=username).first():
                flash("Ce nom d'utilisateur existe déjà", "error")
                return render_template('signup.html')
                
            if User.query.filter_by(email=email).first():
                flash("Cet email est déjà utilisé", "error")
                return render_template('signup.html')
            
            # Création de l'utilisateur
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_doctor=is_doctor,
                doctor_status='pending' if is_doctor else None
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'inscription : {str(e)}")
            flash("Une erreur est survenue lors de l'inscription. Veuillez réessayer.", "error")
            return render_template('signup.html')
        
    return render_template('signup.html')

@app.route('/chat_user')
@login_required
def chat_user():
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    chat_id = request.args.get('chat_id')
    if chat_id:
        current_chat = Chat.query.get(chat_id)
        if not current_chat or current_chat.user_id != current_user.id:
            # Si le chat n'existe pas ou n'appartient pas à l'utilisateur, créer un nouveau chat
            new_chat = Chat(user_id=current_user.id)
            db.session.add(new_chat)
            db.session.commit()
            current_chat = new_chat
    else:
        # Créer une nouvelle conversation si aucun chat_id n'est fourni
        new_chat = Chat(user_id=current_user.id)
        db.session.add(new_chat)
        db.session.commit()
        current_chat = new_chat
    
    # Récupérer tous les chats de l'utilisateur
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    
    # Récupérer les messages du chat actuel
    messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at.asc()).all()
    
    return render_template('chat_user.html', 
                         current_user=current_user,
                         chats=chats,
                         current_chat=current_chat,
                         messages=messages)

@app.route('/chat_history')
@login_required
def chat_history():
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat_history.html', 
                         current_user=current_user,
                         chats=chats)

@app.route('/chat_doctor')
@doctor_required
def chat_doctor():
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    # Récupérer tous les chats des utilisateurs
    chats = Chat.query.order_by(Chat.created_at.desc()).all()
    
    # Si aucun chat n'existe, créer un nouveau chat
    if not chats:
        new_chat = Chat(user_id=current_user.id)
        db.session.add(new_chat)
        db.session.commit()
        chats = [new_chat]
    
    # Récupérer le chat actuel (premier chat par défaut)
    current_chat = chats[0]
    
    # Récupérer les messages du chat actuel
    messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at.asc()).all()
    
    return render_template('chat_doctor.html',
                         current_user=current_user,
                         chats=chats,
                         current_chat=current_chat,
                         messages=messages)

@app.route('/chat_admin')
@admin_required
def chat_admin():
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    chat_id = request.args.get('chat_id')
    if chat_id:
        current_chat = Chat.query.get(chat_id)
        if not current_chat:
            # Si le chat n'existe pas, créer un nouveau chat
            new_chat = Chat(user_id=current_user.id)
            db.session.add(new_chat)
            db.session.commit()
            current_chat = new_chat
    else:
        # Créer une nouvelle conversation si aucun chat_id n'est fourni
        new_chat = Chat(user_id=current_user.id)
        db.session.add(new_chat)
        db.session.commit()
        current_chat = new_chat
    
    # Récupérer tous les chats
    chats = Chat.query.order_by(Chat.created_at.desc()).all()
    
    # Récupérer les messages du chat actuel
    messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at.asc()).all()
    
    return render_template('chat_admin.html',
                         current_user=current_user,
                         chats=chats,
                         current_chat=current_chat,
                         messages=messages)

@app.route('/api/admin/chats/<int:chat_id>/end', methods=['POST'])
@admin_required
def end_admin_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    try:
        # Marquer le chat comme terminé
        chat.status = 'ended'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la fermeture de la conversation : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la fermeture de la conversation'}), 500

@app.route('/doctor_dashboard')
@doctor_required
def doctor_dashboard():
    return render_template('doctor_interface.html')

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    if not google_api_key:
        return jsonify({
            'error': 'Configuration Google manquante',
            'message': 'Veuillez configurer votre clé API Google dans le fichier .env'
        }), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400

    user_message = data.get('message')
    chat_id = data.get('chat_id')
    
    if not user_message:
        return jsonify({'error': 'Message manquant'}), 400
    
    try:
        # Créer un nouveau chat si nécessaire
        if not chat_id:
            chat = Chat(user_id=session['user_id'])
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        # Sauvegarder le message de l'utilisateur
        user_msg = Message(
            chat_id=chat_id,
            content=user_message,
            sender_type='user'
        )
        db.session.add(user_msg)
        
        # Générer la réponse du chatbot
        bot_response = chatbot.generate_response(user_message, session.get('is_doctor', False))
        
        # Sauvegarder la réponse du bot
        bot_msg = Message(
            chat_id=chat_id,
            content=bot_response,
            sender_type='bot'
        )
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'chat_id': chat_id,
            'response': bot_response
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'envoi du message : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de l\'envoi du message'}), 500

@app.route('/get_conversation_summary')
@login_required
def get_conversation_summary():
    return jsonify({'summary': chatbot.get_conversation_summary()})

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_interface():
    return render_template('admin_interface.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get some statistics for the dashboard
    total_users = User.query.filter_by(is_doctor=False, is_admin=False).count()
    total_doctors = User.query.filter_by(is_doctor=True).count()
    total_chats = Chat.query.count()
    total_messages = Message.query.count()
    
    # Get recent activities
    recent_chats = Chat.query.order_by(Chat.created_at.desc()).limit(5).all()
    recent_doctors = User.query.filter_by(is_doctor=True).order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         current_user=current_user,
                         total_users=total_users,
                         total_doctors=total_doctors,
                         total_chats=total_chats,
                         total_messages=total_messages,
                         recent_chats=recent_chats,
                         recent_doctors=recent_doctors)

@app.route('/api/admin/doctors')
@admin_required
def get_doctors():
    status = request.args.get('status', 'pending')
    doctors = User.query.filter_by(is_doctor=True, doctor_status=status).all()
    return jsonify([{
        'id': doctor.id,
        'username': doctor.username,
        'email': doctor.email,
        'status': doctor.doctor_status,
        'created_at': doctor.created_at.isoformat()
    } for doctor in doctors])

@app.route('/api/admin/doctors/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor_status(doctor_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Statut manquant'}), 400

    status = data['status']
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    doctor = User.query.get_or_404(doctor_id)
    if not doctor.is_doctor:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    try:
        doctor.doctor_status = status
        db.session.commit()
        return jsonify({'message': 'Statut mis à jour avec succès'})
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du statut : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la mise à jour du statut'}), 500

@app.route('/api/admin/doctors/<int:doctor_id>', methods=['DELETE'])
@admin_required
def delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    if not doctor.is_doctor:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    try:
        db.session.delete(doctor)
        db.session.commit()
        return jsonify({'message': 'Médecin supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la suppression du médecin : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la suppression du médecin'}), 500

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.is_doctor = request.form.get('is_doctor') == 'on'
            user.is_admin = request.form.get('is_admin') == 'on'
            if request.form.get('password'):
                user.password_hash = generate_password_hash(request.form.get('password'))
            db.session.commit()
            flash("Utilisateur mis à jour avec succès.", "success")
            return redirect(url_for('admin_interface'))
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour de l'utilisateur : {str(e)}")
            flash("Une erreur est survenue lors de la mise à jour de l'utilisateur.", "error")
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != session['user_id']:  # Empêcher l'auto-suppression
        try:
            db.session.delete(user)
            db.session.commit()
            flash("Utilisateur supprimé avec succès.", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la suppression de l'utilisateur : {str(e)}")
            flash("Une erreur est survenue lors de la suppression de l'utilisateur.", "error")
    return redirect(url_for('admin_interface'))

@app.route('/admin/chat/<int:chat_id>')
@admin_required
def admin_view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    return render_template('admin_view_chat.html', chat=chat)

@app.route('/create_admin', methods=['GET'])
def create_admin():
    try:
        # Vérifier si un admin existe déjà
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            return "Un administrateur existe déjà dans la base de données."
        
        # Créer un nouvel admin
        admin = User(
            username="admin",
            email="admin@medical.com",
            password_hash=generate_password_hash("admin123"),
            is_admin=True,
            is_doctor=False,
            doctor_status=None
        )
        
        db.session.add(admin)
        db.session.commit()
        return "Compte administrateur créé avec succès. Email: admin@medical.com, Mot de passe: admin123"
    except Exception as e:
        db.session.rollback()
        return f"Erreur lors de la création du compte admin: {str(e)}"

@app.route('/api/chat/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != session['user_id']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Supprimer d'abord tous les messages associés
        Message.query.filter_by(chat_id=chat_id).delete()
        # Puis supprimer le chat
        db.session.delete(chat)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la suppression de la conversation : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la suppression de la conversation'}), 500

@app.route('/api/doctor/medicines', methods=['GET', 'POST'])
@doctor_required
def manage_medicines():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'name' not in data or 'description' not in data:
                return jsonify({'error': 'Données manquantes'}), 400

            # Vérifier si le médicament existe déjà
            existing_medicine = Medicine.query.filter_by(name=data['name']).first()
            if existing_medicine:
                return jsonify({'error': 'Ce médicament existe déjà'}), 400

            # Créer le nouveau médicament
            medicine = Medicine(
                name=data['name'],
                description=data['description'],
                created_by=session['user_id']
            )
            
            db.session.add(medicine)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'medicine': {
                    'id': medicine.id,
                    'name': medicine.name,
                    'description': medicine.description,
                    'created_at': medicine.created_at.isoformat()
                }
            })
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'ajout du médicament : {str(e)}")
            return jsonify({'error': 'Une erreur est survenue lors de l\'ajout du médicament'}), 500
    
    # GET - Récupérer la liste des médicaments
    try:
        medicines = Medicine.query.order_by(Medicine.created_at.desc()).all()
        return jsonify({
            'success': True,
            'medicines': [{
                'id': m.id,
                'name': m.name,
                'description': m.description,
                'created_at': m.created_at.isoformat()
            } for m in medicines]
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des médicaments : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la récupération des médicaments'}), 500

@app.route('/api/doctor/medicines/<int:medicine_id>', methods=['DELETE'])
@doctor_required
def delete_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    if medicine.created_by != session['user_id']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        db.session.delete(medicine)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la suppression du médicament : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la suppression du médicament'}), 500

@app.route('/api/doctor/medicines/<int:medicine_id>', methods=['PUT'])
@doctor_required
def update_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    if medicine.created_by != session['user_id']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['name', 'description']):
            return jsonify({'error': 'Données manquantes'}), 400

        # Vérifier si le nouveau nom existe déjà (sauf pour le médicament actuel)
        existing_medicine = Medicine.query.filter(
            Medicine.name == data['name'],
            Medicine.id != medicine_id
        ).first()
        if existing_medicine:
            return jsonify({'error': 'Ce nom de médicament existe déjà'}), 400

        # Mettre à jour les champs
        medicine.name = data['name']
        medicine.description = data['description']
        
        db.session.commit()
        return jsonify({
            'success': True,
            'medicine': {
                'id': medicine.id,
                'name': medicine.name,
                'description': medicine.description,
                'created_at': medicine.created_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du médicament : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la mise à jour du médicament'}), 500

@app.route('/api/doctor/diseases', methods=['GET', 'POST'])
@doctor_required
def manage_diseases():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Données manquantes'}), 400

            # Create new disease record with ID
            new_disease = {
                "id": len(load_medical_data()),  # Generate sequential ID
                "Maladie": data.get('Maladie'),
                "Description": data.get('Description'),
                "Symptômes": data.get('Symptômes', []),
                "Urgence": data.get('Urgence'),
                "Médicaments": data.get('Médicaments', []),
                "Actions recommandées": data.get('Actions recommandées')
            }
            
            # Load existing data
            medical_data = load_medical_data()
            medical_data.append(new_disease)
            save_medical_data(medical_data)
            
            return jsonify({
                'success': True,
                'message': 'Dossier médical ajouté avec succès',
                'disease': new_disease
            })
        except Exception as e:
            print(f"Erreur lors de l'ajout du dossier médical : {str(e)}")
            return jsonify({'error': 'Une erreur est survenue lors de l\'ajout du dossier médical'}), 500
    
    # GET - Récupérer la liste des maladies
    try:
        medical_data = load_medical_data()
        return jsonify({
            'success': True,
            'diseases': medical_data
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des dossiers médicaux : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la récupération des dossiers médicaux'}), 500

@app.route('/api/doctor/diseases/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@doctor_required
def manage_disease(id):
    try:
        medical_data = load_medical_data()
        
        # Find the disease by ID
        disease = next((d for d in medical_data if d.get('id') == id), None)
        
        if not disease:
            return jsonify({
                'success': False,
                'error': 'Dossier médical non trouvé'
            }), 404

        if request.method == 'DELETE':
            medical_data = [d for d in medical_data if d.get('id') != id]
            save_medical_data(medical_data)
            return jsonify({
                'success': True,
                'message': 'Dossier médical supprimé avec succès'
            })
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'disease': disease
            })
        
        # PUT - Mise à jour du dossier médical
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Données manquantes'}), 400

            # Update the disease data
            disease.update({
                "Maladie": data.get('Maladie'),
                "Description": data.get('Description'),
                "Symptômes": data.get('Symptômes', []),
                "Urgence": data.get('Urgence'),
                "Médicaments": data.get('Médicaments', []),
                "Actions recommandées": data.get('Actions recommandées')
            })
            
            # Update the medical data
            medical_data = [d if d.get('id') != id else disease for d in medical_data]
            save_medical_data(medical_data)
            
            return jsonify({
                'success': True,
                'message': 'Dossier médical mis à jour avec succès',
                'disease': disease
            })
                
    except Exception as e:
        print(f"Erreur lors de la gestion du dossier médical : {str(e)}")
        return jsonify({'error': 'Une erreur est survenue lors de la gestion du dossier médical'}), 500

@app.route('/doctor')
def doctor_interface():
    return render_template('doctor_interface.html')

def load_medical_data():
    try:
        with open('medical_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_medical_data(data):
    with open('medical_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Vérifier si un admin existe déjà
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            # Créer un compte admin par défaut
            admin = User(
                username="admin",
                email="admin@medical.com",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                is_doctor=False,
                doctor_status=None
            )
            db.session.add(admin)
            db.session.commit()
        print("Compte admin créé :")
        print("Username: admin")
        print("Password: admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 