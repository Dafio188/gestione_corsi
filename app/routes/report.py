from flask import Blueprint, render_template
from app.models import db  # ✅ Importa `db`
from app.models.models import Iscrizione, Discente, Corso, Lezione, Presenza

report_bp = Blueprint('report', __name__, url_prefix='/report')


# 🔹 Report Generale delle Presenze
@report_bp.route('/')
def report_generale():
    presenze = Presenza.query.all()
    return render_template('report.html', presenze=presenze)

# 🔹 Report delle Iscrizioni
@report_bp.route('/iscrizioni')
def report_iscrizioni():
    iscrizioni = Iscrizione.query.all()
    return render_template('report_iscrizioni.html', iscrizioni=iscrizioni)

# 🔹 Report dei Discenti iscritti ai Corsi
@report_bp.route('/discenti_corsi')
def report_discenti_corsi():
    discenti = Discente.query.all()
    corsi = Corso.query.all()
    return render_template('report_discenti_corsi.html', discenti=discenti, corsi=corsi)

# 🔹 Report delle Lezioni
@report_bp.route('/lezioni')
def report_lezioni():
    lezioni = Lezione.query.all()
    return render_template('report_lezioni.html', lezioni=lezioni)

# 🔹 Report Completo (Unione di tutti i dati)
@report_bp.route('/completo')
def report_completo():
    iscrizioni = Iscrizione.query.all()
    discenti = Discente.query.all()
    corsi = Corso.query.all()
    lezioni = Lezione.query.all()
    presenze = Presenza.query.all()
    
    return render_template(
        'report_completo.html',
        iscrizioni=iscrizioni,
        discenti=discenti,
        corsi=corsi,
        lezioni=lezioni,
        presenze=presenze
    )
