# Import directly from app.py instead of from an app package
import sys
import os
import shutil

# Temporarily rename the app directory to avoid import confusion
app_dir = os.path.join(os.path.dirname(__file__), 'app')
temp_app_dir = os.path.join(os.path.dirname(__file__), 'app_temp')
app_dir_renamed = False

if os.path.exists(app_dir):
    print(f"Temporarily renaming app directory to avoid import confusion")
    try:
        if os.path.exists(temp_app_dir):
            shutil.rmtree(temp_app_dir)
        shutil.move(app_dir, temp_app_dir)
        app_dir_renamed = True
    except Exception as e:
        print(f"Warning: Could not rename app directory: {e}")

try:
    # Create a simple Flask app and database for initialization
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from werkzeug.security import generate_password_hash

    # Create a simple Flask app
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = 'your-secret-key-here'
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db = SQLAlchemy(flask_app)
    
    # Define User model
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(100), unique=True, nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=False)
        password_hash = db.Column(db.String(200), nullable=False)
        nome = db.Column(db.String(100), nullable=False)
        cognome = db.Column(db.String(100), nullable=False)
        role = db.Column(db.String(20), nullable=False, default='discente')
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
    
    # Define other models
    class Corso(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        titolo = db.Column(db.String(200), nullable=False)
        descrizione = db.Column(db.Text, nullable=True)
        ore_totali = db.Column(db.Float, nullable=False)
        data_inizio = db.Column(db.DateTime, nullable=False)
        data_fine = db.Column(db.DateTime, nullable=False)
        progetto_riferimento = db.Column(db.String(200), nullable=True)
        docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        
        docente = db.relationship('User', backref=db.backref('corsi', lazy=True))

    class Iscrizione(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        discente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
        ore_frequentate = db.Column(db.Float, default=0)
        
        discente = db.relationship('User', backref=db.backref('iscrizioni', lazy=True))
        corso = db.relationship('Corso', backref=db.backref('iscrizioni', lazy=True))

    class Test(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
        tipo = db.Column(db.String(50), nullable=False)
        titolo = db.Column(db.String(200), nullable=False)
        file_path = db.Column(db.String(255), nullable=True)
        forms_link = db.Column(db.String(255), nullable=True)
        
        corso = db.relationship('Corso', backref=db.backref('test', lazy=True))

    class RisultatoTest(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
        iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
        punteggio = db.Column(db.Float, nullable=False)
        data_completamento = db.Column(db.DateTime, nullable=True)
        
        test = db.relationship('Test', backref=db.backref('risultati', lazy=True))
        iscrizione = db.relationship('Iscrizione', backref=db.backref('risultati_test', lazy=True))

    class Attestato(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
        file_path = db.Column(db.String(255), nullable=True)
        data_generazione = db.Column(db.DateTime, nullable=True)
        
        iscrizione = db.relationship('Iscrizione', backref=db.backref('attestato', uselist=False))
    
    from run import app, db, User

    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                nome='Admin',
                cognome='User',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
        
        print("Database initialized successfully!")
        
        print('Database initialized!')

except Exception as e:
    print(f"Error during database initialization: {e}")
    
finally:
    # Restore the app directory if it was renamed
    if app_dir_renamed:
        try:
            shutil.move(temp_app_dir, app_dir)
            print("Restored app directory")
        except Exception as e:
            print(f"Warning: Could not restore app directory: {e}")