from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

class Progetto(db.Model):
    __tablename__ = 'progetto'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text)
    data_inizio = db.Column(db.DateTime)
    data_fine = db.Column(db.DateTime)
    budget = db.Column(db.Float)
    
    # Fix relationships to avoid conflicts
    corsi = db.relationship('Corso', backref='progetto_ref', lazy=True, foreign_keys='Corso.progetto_id', overlaps="corsi_list,progetto")

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
    eta = db.Column(db.String(50), nullable=True)
    ruolo_ente = db.Column(db.String(100), nullable=True)
    unita_org = db.Column(db.String(100), nullable=True)
    dipartimento = db.Column(db.String(100), nullable=True)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=True)
    
    # Fix relationship to avoid conflicts
    progetto_assegnato = db.relationship('Progetto', foreign_keys=[progetto_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    materiale = db.Column(db.String(255), nullable=True)
    
    # Fix relationships to avoid conflicts
    docente = db.relationship('User', backref='corsi_insegnati')
    iscrizioni = db.relationship('Iscrizione', backref='corso_ref', cascade='all, delete-orphan')
    test = db.relationship('Test', backref='test_parent', cascade='all, delete-orphan', overlaps="test_list,test_association,test_parent")
    
    # Add this direct relationship to access the progetto directly
    progetto = db.relationship('Progetto', foreign_keys=[progetto_id], backref='corsi_list', overlaps="corsi,progetto_ref,corsi_list")
    test_list = db.relationship('Test', backref='test_association', overlaps="test_list,test_association,corso_parent")

class Iscrizione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    ore_frequentate = db.Column(db.Float, default=0)
    
    discente = db.relationship('User', backref=db.backref('iscrizioni', lazy=True))
    # Relationship is defined in Corso class

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'ingresso', 'intermedio', 'finale'
    titolo = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    forms_link = db.Column(db.String(255), nullable=True)
    
    # Add this relationship to access the corso directly
    corso = db.relationship('Corso', foreign_keys=[corso_id], backref='test_association', overlaps="corso_parent,test,test_association")
    
    # Relationship is defined in Corso class
    
class Nota(db.Model):
    __tablename__ = 'nota'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    contenuto = db.Column(db.Text, nullable=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    data_modifica = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=True)
    
    docente = db.relationship('User', backref=db.backref('note', lazy=True))
    corso = db.relationship('Corso', backref=db.backref('note', lazy=True))

class RisultatoTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    punteggio = db.Column(db.Float, nullable=False)
    superato = db.Column(db.Boolean, default=False)
    data_completamento = db.Column(db.DateTime, default=datetime.utcnow)
    
    test = db.relationship('Test', backref=db.backref('risultati', lazy=True))
    iscrizione = db.relationship('Iscrizione', backref=db.backref('risultati_test', lazy=True))

class Attestato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    data_generazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    iscrizione = db.relationship('Iscrizione', backref=db.backref('attestato', uselist=False))