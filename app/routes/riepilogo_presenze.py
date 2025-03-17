from flask import Blueprint, render_template
from app.models.models import db, Iscrizione, Discente, Corso, Presenza, Lezione

riepilogo_presenze_bp = Blueprint('riepilogo_presenze', __name__)

@riepilogo_presenze_bp.route('/')
def riepilogo():
    corsi = Corso.query.all()
    discenti = Discente.query.all()
    riepilogo_presenze = []

    for discente in discenti:
        for corso in corsi:
            iscrizione = Iscrizione.query.filter_by(discente_id=discente.id, corso_id=corso.id).first()
            if iscrizione:
                lezioni_totali = Lezione.query.filter_by(corso_id=corso.id).count()
                presenze_effettuate = Presenza.query.filter_by(discente_id=discente.id).count()
                percentuale_presenza = (presenze_effettuate / lezioni_totali) * 100 if lezioni_totali > 0 else 0

                riepilogo_presenze.append({
                    'discente': f"{discente.nome} {discente.cognome}",
                    'corso': corso.nome,
                    'ore_frequentate': iscrizione.ore_frequentate,
                    'percentuale_presenza': round(percentuale_presenza, 2)
                })

    return render_template('riepilogo_presenze.html', riepilogo_presenze=riepilogo_presenze)
