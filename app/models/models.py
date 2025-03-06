from flask_sqlalchemy import SQLAlchemy
from datetime import date  # Per gestire le date

db = SQLAlchemy()

class Lezione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    data_lezione = db.Column(db.Date, nullable=False)
    orario = db.Column(db.String(50), nullable=False)  # Mattina/Pomeriggio

    corso = db.relationship('Corso', backref=db.backref('lezioni', lazy=True))

class Presenza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lezione_id = db.Column(db.Integer, db.ForeignKey('lezione.id'), nullable=False)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    presente = db.Column(db.Boolean, default=False)

    lezione = db.relationship('Lezione', backref=db.backref('presenze', lazy=True))
    discente = db.relationship('Discente', backref=db.backref('presenze', lazy=True))

class Attestato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_discente = db.Column(db.String(100), nullable=False)
    corso = db.Column(db.String(100), nullable=False)
    data_attestato = db.Column(db.Date, nullable=False)

class Progetto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    ente = db.Column(db.String(100))
    inizio_progetto = db.Column(db.Date)
    fine_progetto = db.Column(db.Date)

    corsi = db.relationship('Corso', backref='progetto', lazy=True, overlaps="progetto_associazione")

class Corso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    docente = db.Column(db.String(100), nullable=False)
    ore_totali = db.Column(db.Integer, nullable=False)
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=False)

    test_risultati = db.relationship('TestRisultato', back_populates='corso_test', lazy=True)


class Discente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    codice_fiscale = db.Column(db.String(16), unique=True, nullable=False)
    genere = db.Column(db.String(10))
    fascia_eta = db.Column(db.String(50))
    ruolo = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    cellulare = db.Column(db.String(20))
    progetto_id = db.Column(db.Integer, db.ForeignKey('progetto.id'), nullable=False)

    # 🔹 Aggiunto il collegamento con Iscrizione per accedere direttamente ai corsi
    iscrizioni = db.relationship('Iscrizione', backref='discente', lazy=True)
    progetto = db.relationship('Progetto', backref='discenti')

class Iscrizione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    ore_frequentate = db.Column(db.Integer, default=0)
    test_superato = db.Column(db.Boolean, default=False)
    punteggio_test = db.Column(db.Integer, default=0)
    corso = db.relationship('Corso', backref='iscrizioni')

# Nuova tabella per salvare i risultati dei test
class TestRisultato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discente_id = db.Column(db.Integer, db.ForeignKey('discente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.id'), nullable=False)
    punteggio_ottenuto = db.Column(db.Integer, nullable=False)
    superato = db.Column(db.Boolean, nullable=False)

    # Relazioni con discente e corso
    discente = db.relationship('Discente', backref=db.backref('test_risultati', lazy=True))
    corso_test = db.relationship('Corso', back_populates='test_risultati', lazy=True)

