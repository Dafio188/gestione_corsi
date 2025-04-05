from app import db
from datetime import datetime

class Prenotazione(db.Model):
    __tablename__ = 'prenotazioni'
    
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corsi.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='disponibile')  # disponibile, occupato, annullato
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazioni
    docente = db.relationship('User', backref='prenotazioni')
    corso = db.relationship('Corso', backref='prenotazioni')

    @staticmethod
    def is_available(start, end, docente_id):
        """Verifica se l'orario è disponibile per il docente"""
        return not Prenotazione.query.filter(
            Prenotazione.docente_id == docente_id,
            Prenotazione.status != 'annullato',
            Prenotazione.start < end,
            Prenotazione.end > start
        ).first()

    def to_dict(self):
        """Converte la prenotazione in un dizionario per l'API"""
        return {
            'id': self.id,
            'title': self.title,
            'start': self.start.isoformat(),
            'end': self.end.isoformat(),
            'status': self.status,
            'docente_id': self.docente_id,
            'corso_id': self.corso_id,
            'note': self.note,
            'className': self.status  # per FullCalendar
        } 