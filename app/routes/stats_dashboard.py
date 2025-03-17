from flask import Blueprint, render_template, jsonify
from app.models.models import db, Iscrizione, Discente, Corso, Presenza, Lezione

stats_dashboard_bp = Blueprint('stats_dashboard', __name__)

@stats_dashboard_bp.route('/')
def dashboard():
    return render_template('stats_dashboard.html')

@stats_dashboard_bp.route('/dati_presenze')
def dati_presenze():
    corsi = Corso.query.all()
    data = []

    for corso in corsi:
        lezioni_totali = Lezione.query.filter_by(corso_id=corso.id).count()
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()

        for iscrizione in iscrizioni:
            discente = Discente.query.get(iscrizione.discente_id)
            presenze_effettuate = Presenza.query.filter_by(discente_id=discente.id).count()
            percentuale_presenza = (presenze_effettuate / lezioni_totali) * 100 if lezioni_totali > 0 else 0

            data.append({
                'corso': corso.nome,
                'discente': f"{discente.nome} {discente.cognome}",
                'percentuale_presenza': round(percentuale_presenza, 2)
            })

    return jsonify(data)
