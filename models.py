from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

class Progetto(db.Model):
    __tablename__ = 'progetto'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text)
    data_inizio = db.Column(db.Date)
    data_fine = db.Column(db.Date)
    budget = db.Column(db.Float, default=0.0)
    link_corso = db.Column(db.String(500))
    stato = db.Column(db.String(50), default='attivo')
    corsi = db.relationship('Corso', back_populates='progetto', lazy=True)
    discenti = db.relationship('User', back_populates='progetto_assegnato', lazy=True)
    note = db.relationship('Nota', back_populates='progetto', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    ruolo = db.Column(db.String(20), nullable=False, default='discente')
    
    # Alias per compatibilità con il codice esistente
    @property
    def role(self):
        return self.ruolo
    
    @role.setter
    def role(self, value):
        self.ruolo = value
    
    # Campi aggiuntivi per i discenti
    codice_fiscale = db.Column(db.String(16), nullable=True)
    eta = db.Column(db.String(50), nullable=True)
    ruolo_ente = db.Column(db.String(100), nullable=True)
    unita_org = db.Column(db.String(100), nullable=True)
    dipartimento = db.Column(db.String(100), nullable=True)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=True)
    
    # Fix relationship to avoid conflicts
    progetto_assegnato = db.relationship('Progetto', back_populates='discenti', foreign_keys=[progetto_id])
    corsi_docente = db.relationship('Corso', back_populates='docente')
    iscrizioni = db.relationship('Iscrizione', back_populates='discente', lazy=True)
    note = db.relationship('Nota', back_populates='docente', lazy=True)
    disponibilita = db.relationship('DisponibilitaDocente', back_populates='docente', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Corso(db.Model):
    __tablename__ = 'corso'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text)
    data_inizio = db.Column(db.Date)
    data_fine = db.Column(db.Date)
    ore_totali = db.Column(db.Integer)
    stato = db.Column(db.String(50), default='attivo')
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'))
    progetto = db.relationship('Progetto', back_populates='corsi')
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    docente = db.relationship('User', back_populates='corsi_docente')
    iscrizioni = db.relationship('Iscrizione', back_populates='corso', lazy=True)
    test = db.relationship('Test', back_populates='corso', lazy=True)
    note = db.relationship('Nota', back_populates='corso', lazy=True)
    attestati = db.relationship('Attestato', back_populates='corso', lazy=True)
    disponibilita = db.relationship('DisponibilitaDocente', back_populates='corso', lazy=True)
    progetto_riferimento = db.Column(db.String(200))
    
    # Campi per modalità
    modalita = db.Column(db.String(20), default='in_house')
    indirizzo = db.Column(db.String(200))
    link_webinar = db.Column(db.String(200))
    piattaforma = db.Column(db.String(200))
    orario = db.Column(db.String(100))
    materiale = db.Column(db.String(255), nullable=True)

class Iscrizione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    ore_frequentate = db.Column(db.Float, default=0)
    
    discente = db.relationship('User', back_populates='iscrizioni')
    corso = db.relationship('Corso', back_populates='iscrizioni')
    risultati_test = db.relationship('RisultatoTest', back_populates='iscrizione', lazy=True)
    attestato = db.relationship('Attestato', back_populates='iscrizione', uselist=False)
    
    @property
    def corso_ref(self):
        return self.corso

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'ingresso', 'intermedio', 'finale'
    titolo = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    forms_link = db.Column(db.String(255), nullable=True)
    
    corso = db.relationship('Corso', back_populates='test')
    risultati = db.relationship('RisultatoTest', back_populates='test', lazy=True)

class Nota(db.Model):
    __tablename__ = 'nota'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    contenuto = db.Column(db.Text, nullable=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    data_modifica = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=True)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=True)
    
    docente = db.relationship('User', back_populates='note')
    corso = db.relationship('Corso', back_populates='note')
    progetto = db.relationship('Progetto', back_populates='note')

class RisultatoTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    punteggio = db.Column(db.Float, nullable=False)
    superato = db.Column(db.Boolean, default=False)
    data_completamento = db.Column(db.DateTime, default=datetime.utcnow)
    
    test = db.relationship('Test', back_populates='risultati')
    iscrizione = db.relationship('Iscrizione', back_populates='risultati_test')

class Attestato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iscrizione_id = db.Column(db.Integer, db.ForeignKey('iscrizione.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    data_generazione = db.Column(db.DateTime, default=datetime.utcnow)
    badge_exported = db.Column(db.Boolean, default=False)
    public_token = db.Column(db.String(100), unique=True, nullable=True)
    
    iscrizione = db.relationship('Iscrizione', back_populates='attestato')
    corso = db.relationship('Corso', back_populates='attestati')

class DisponibilitaDocente(db.Model):
    __tablename__ = 'disponibilita_docente'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    ora_inizio = db.Column(db.Time, nullable=False)
    ora_fine = db.Column(db.Time, nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'))
    note = db.Column(db.Text)
    stato = db.Column(db.String(20), default='disponibile')  # disponibile, occupato, annullato
    
    docente = db.relationship('User', back_populates='disponibilita')
    corso = db.relationship('Corso', back_populates='disponibilita')
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario per la serializzazione JSON"""
        # Verifica se il docente esiste
        docente_nome = "Docente non trovato"
        if self.docente:
            docente_nome = f"{self.docente.nome} {self.docente.cognome}"
            
        # Verifica se il corso esiste
        corso_titolo = None
        if self.corso:
            corso_titolo = self.corso.titolo
            
        return {
            'id': self.id,
            'title': docente_nome,
            'start': f"{self.data.isoformat()}T{self.ora_inizio.isoformat()}",
            'end': f"{self.data.isoformat()}T{self.ora_fine.isoformat()}",
            'className': self.stato,
            'extendedProps': {
                'docente_id': self.docente_id,
                'corso_id': self.corso_id,
                'corso': corso_titolo,
                'stato': self.stato,
                'note': self.note
            }
        }
    
    @staticmethod
    def is_available(start_datetime, end_datetime, docente_id):
        """Verifica se un docente è disponibile in un determinato periodo"""
        # Verifica sovrapposizioni
        sovrapposizioni = DisponibilitaDocente.query.filter(
            DisponibilitaDocente.docente_id == docente_id,
            DisponibilitaDocente.data == start_datetime.date(),
            DisponibilitaDocente.stato != 'annullato',
            db.or_(
                db.and_(
                    DisponibilitaDocente.ora_inizio <= start_datetime.time(),
                    DisponibilitaDocente.ora_fine > start_datetime.time()
                ),
                db.and_(
                    DisponibilitaDocente.ora_inizio < end_datetime.time(),
                    DisponibilitaDocente.ora_fine >= end_datetime.time()
                ),
                db.and_(
                    DisponibilitaDocente.ora_inizio >= start_datetime.time(),
                    DisponibilitaDocente.ora_fine <= end_datetime.time()
                )
            )
        ).count()
        
        return sovrapposizioni == 0

class DisponibilitaDiscente(db.Model):
    __tablename__ = 'disponibilita_discente'
    
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    ora_inizio = db.Column(db.Time, nullable=False)
    ora_fine = db.Column(db.Time, nullable=False)
    note = db.Column(db.Text)
    stato = db.Column(db.String(20), default='disponibile')  # disponibile, confermata, annullata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    discente = db.relationship('User', backref='disponibilita_discente')

class Evento(db.Model):
    __tablename__ = 'evento'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text)
    data_inizio = db.Column(db.DateTime, nullable=False)
    data_fine = db.Column(db.DateTime, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # lezione, riunione, altro
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    corso = db.relationship('Corso', backref='eventi')
    docente = db.relationship('User', backref='eventi')