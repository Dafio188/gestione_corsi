from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

# In the Progetto class
# Look for the Progetto class in your models.py file and update it
class Progetto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)  # Changed from 'nome' to 'titolo'
    descrizione = db.Column(db.Text)
    data_inizio = db.Column(db.DateTime)
    data_fine = db.Column(db.DateTime)
    
    # Remove the backref from this relationship since it's defined in Corso
    corsi = db.relationship('Corso', lazy=True,
                           primaryjoin="Progetto.id==Corso.progetto_id")

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='discente')
    
    # Campi aggiuntivi per i discenti
    codice_fiscale = db.Column(db.String(16), nullable=True)
    eta = db.Column(db.String(50), nullable=True)  # Modificato da Integer a String(50)
    ruolo_ente = db.Column(db.String(100), nullable=True)
    unita_org = db.Column(db.String(100), nullable=True)
    dipartimento = db.Column(db.String(100), nullable=True)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=True)
    
    # Relazione con il progetto
    progetto = db.relationship('Progetto', backref=db.backref('discenti', lazy=True), foreign_keys=[progetto_id])
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# In the Corso class
class Corso(db.Model):
    __tablename__ = 'corso'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    ore_totali = db.Column(db.Float, nullable=False)
    data_inizio = db.Column(db.DateTime, nullable=False)
    data_fine = db.Column(db.DateTime, nullable=False)
    
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=True)
    progetto_riferimento = db.Column(db.String(100))
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Campi per modalità
    modalita = db.Column(db.String(20), default='in_house')
    indirizzo = db.Column(db.String(200))
    link_webinar = db.Column(db.String(200))
    piattaforma = db.Column(db.String(200))
    orario = db.Column(db.String(100))
    
    # Fix relationships - remove duplicates and fix backref names
    docente = db.relationship('User', backref='corsi_insegnati')
    progetto = db.relationship('Progetto', backref='corsi_list')
    iscrizioni = db.relationship('Iscrizione', backref='corso_ref', cascade='all, delete-orphan')
    test = db.relationship('Test', backref='corso_parent', cascade='all, delete-orphan')

class Iscrizione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    ore_frequentate = db.Column(db.Float, default=0)
    
    discente = db.relationship('User', backref=db.backref('iscrizioni', lazy=True))
    # Fix relationship - remove backref and overlaps
    corso = db.relationship('Corso', foreign_keys=[corso_id])

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    titolo = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    forms_link = db.Column(db.String(255), nullable=True)
    
    # Fix relationship - remove backref and overlaps
    corso = db.relationship('Corso', foreign_keys=[corso_id])
    tipo = db.Column(db.String(50), nullable=False)  # 'ingresso', 'intermedio', 'finale'
    titolo = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    forms_link = db.Column(db.String(255), nullable=True)
    
    # Add overlaps parameter to fix warnings
    corso = db.relationship('Corso', backref=db.backref('test_list', lazy=True), overlaps="test")
    
class Nota(db.Model):
    __tablename__ = 'nota'  # Add explicit table name
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    contenuto = db.Column(db.Text, nullable=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    data_modifica = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add explicit foreign keys
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=True)
    
    # Define relationships with backref
    docente = db.relationship('User', backref=db.backref('note', lazy=True))
    corso = db.relationship('Corso', backref=db.backref('note', lazy=True))

class RisultatoTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    punteggio = db.Column(db.Float, nullable=False)
    superato = db.Column(db.Boolean, default=False)  # Add this field
    data_completamento = db.Column(db.DateTime, default=datetime.utcnow)
    
    test = db.relationship('Test', backref=db.backref('risultati', lazy=True))
    iscrizione = db.relationship('Iscrizione', backref=db.backref('risultati_test', lazy=True))

class Attestato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    data_generazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    iscrizione = db.relationship('Iscrizione', backref=db.backref('attestato', uselist=False))