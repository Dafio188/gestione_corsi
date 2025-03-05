import os
import pandas as pd
from flask import Blueprint, render_template, send_file, flash
from reportlab.pdfgen import canvas
from app.models.models import db, Iscrizione, Discente, Corso, Presenza, Lezione

report_bp = Blueprint('report', __name__, url_prefix='/report')

REPORT_FOLDER = "app/static/reports"
if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

@report_bp.route('/')
def lista_report():
    return render_template('report.html')

@report_bp.route('/csv_frequenza')
def genera_report_csv_frequenza():
    iscrizioni = Iscrizione.query.all()
    data = []

    for iscrizione in iscrizioni:
        discente = Discente.query.get(iscrizione.discente_id)
        corso = Corso.query.get(iscrizione.corso_id)
        lezioni_totali = Lezione.query.filter_by(corso_id=corso.id).count()
        presenze_effettuate = Presenza.query.filter_by(discente_id=discente.id).count()
        percentuale_presenza = (presenze_effettuate / lezioni_totali) * 100 if lezioni_totali > 0 else 0

        data.append({
            'Nome': discente.nome,
            'Cognome': discente.cognome,
            'Codice Fiscale': discente.codice_fiscale,
            'Corso': corso.nome,
            'Ore Frequentate': iscrizione.ore_frequentate,
            'Percentuale Presenza': round(percentuale_presenza, 2)
        })

    df = pd.DataFrame(data)
    filename = os.path.join(REPORT_FOLDER, "report_frequenza.csv")
    df.to_csv(filename, index=False)

    flash('Report CSV sulla frequenza generato con successo!', 'success')
    return send_file(filename, as_attachment=True)

@report_bp.route('/pdf_frequenza')
def genera_report_pdf_frequenza():
    filename = os.path.join(REPORT_FOLDER, "report_frequenza.pdf")
    c = canvas.Canvas(filename)

    c.drawString(100, 800, "Report Frequenza Discenti ai Corsi")
    c.drawString(100, 780, "----------------------------------")

    iscrizioni = Iscrizione.query.all()
    y_position = 760

    for iscrizione in iscrizioni:
        discente = Discente.query.get(iscrizione.discente_id)
        corso = Corso.query.get(iscrizione.corso_id)
        lezioni_totali = Lezione.query.filter_by(corso_id=corso.id).count()
        presenze_effettuate = Presenza.query.filter_by(discente_id=discente.id).count()
        percentuale_presenza = (presenze_effettuate / lezioni_totali) * 100 if lezioni_totali > 0 else 0

        text = f"{discente.nome} {discente.cognome} - {corso.nome} - {percentuale_presenza:.2f}%"
        c.drawString(100, y_position, text)
        y_position -= 20

    c.save()

    flash('Report PDF sulla frequenza generato con successo!', 'success')
    return send_file(filename, as_attachment=True)
