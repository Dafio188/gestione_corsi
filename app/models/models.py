from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import UserMixin
from app.models import db  # Usa l'istanza del database esistente
from werkzeug.security import generate_password_hash, check_password_hash

class Progetto(db.Model):
    __tablename__ = "progetto"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)
    ente = db.Column(db.String(100), nullable=True)
    inizio_progetto = db.Column(db.Date, nullable=True)
    fine_progetto = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<Progetto {self.nome}>"

class Attestato(db.Model):
    __tablename__ = "attestato"
    id = db.Column(db.Integer, primary_key=True)
    nome_discente = db.Column(db.String(100), nullable=False)
    corso = db.Column(db.String(100), nullable=False)
    data_attestato = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<Attestato {self.nome_discente} - {self.corso}>"

class Corso(db.Model):
    __tablename__ = "corso"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)
    test_preliminare = db.Column(db.String(255), nullable=True)  # ✅ Test Iniziale
    test_postcorso = db.Column(db.String(255), nullable=True)  # ✅ Test Finale
    docente = db.Column(db.String(100), nullable=False)
    ore_totali = db.Column(db.Integer, nullable=False)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=False)

    progetto = db.relationship('Progetto', backref=db.backref('corsi', lazy=True))

    def __repr__(self):
        return f"<Corso {self.nome}>"

class RisultatiTestPostCorso(db.Model):
    __tablename__ = "test_risultati_postcorso"
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    risposte = db.Column(db.JSON, nullable=False)
    data_compilazione = db.Column(db.DateTime, default=db.func.current_timestamp())

    discente = db.relationship('Discente', backref=db.backref('test_risultati_postcorso', lazy=True))
    corso = db.relationship('Corso', backref=db.backref('test_risultati_postcorso', lazy=True))

class Discente(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)    
    codice_fiscale = db.Column(db.String(16), unique=True, nullable=False)
    genere = db.Column(db.String(10))
    fascia_eta = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True, nullable=False)  # Aggiunto il campo email
    telefono = db.Column(db.String(20), nullable=True)
    ruolo = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)  # ✅ Campo per la password criptata
    cellulare = db.Column(db.String(20))
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=False)

    progetto = db.relationship('Progetto', backref=db.backref('discenti', lazy=True))

    # ✅ Metodo per impostare la password in modo sicuro
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # ✅ Metodo per verificare la password inserita rispetto a quella salvata
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # 🔹 Qui c'era un errore di troncamento

class Iscrizione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    ore_frequentate = db.Column(db.Integer, default=0)  # 🔹 Ore effettivamente frequentate
    test_superato = db.Column(db.Boolean, default=False)
    punteggio_test = db.Column(db.Integer, default=0)

    discente = db.relationship('Discente', backref=db.backref('iscrizioni', lazy=True))
    corso = db.relationship('Corso', backref=db.backref('iscrizioni', lazy=True))

     # ✅ Metodo per verificare se il discente ha diritto all'attestato
    def puo_ricevere_attestato(self):
        if not self.test_superato:
            return False  # 🔹 Se il test non è segnato come superato, restituisce False

        percentuale_frequenza = (self.ore_frequentate / self.corso.ore_totali) * 100
        return percentuale_frequenza >= 80 and self.punteggio_test >= 85  # 🔹 Entrambe le condizioni devono essere vere

class TestRisultato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    punteggio_ottenuto = db.Column(db.Integer, nullable=False)
    superato = db.Column(db.Boolean, nullable=False)

    discente = db.relationship('Discente', backref=db.backref('test_risultati', lazy=True))
    corso_test = db.relationship('Corso', backref=db.backref('test_risultati', lazy=True))

class Lezione(db.Model):
    __tablename__ = "lezione"
    id = db.Column(db.Integer, primary_key=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    data_lezione = db.Column(db.Date, nullable=False)
    orario = db.Column(db.String(50), nullable=False)  

class Presenza(db.Model):
    __tablename__ = "presenza"
    id = db.Column(db.Integer, primary_key=True)
    lezione_id = db.Column(db.Integer, db.ForeignKey('lezione.id'), nullable=False)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)

    lezione = db.relationship('Lezione', backref=db.backref('presenze', lazy=True))
    discente = db.relationship('Discente', backref=db.backref('presenze', lazy=True))
