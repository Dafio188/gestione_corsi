from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app.models.models import db, Attestato, Iscrizione, Discente, Corso
from reportlab.pdfgen import canvas
import os

attestati_bp = Blueprint('attestati', __name__, url_prefix='/attestati')

PDF_FOLDER = "app/static/attestati"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

@attestati_bp.route('/')
def lista_attestati():
    attestati = Attestato.query.all()
    return render_template('attestati.html', attestati=attestati)

@attestati_bp.route('/genera_pdf/<int:iscrizione_id>')
def genera_pdf(iscrizione_id):
    iscrizione = Iscrizione.query.get(iscrizione_id)
    
    if not iscrizione:
        flash('Errore: Iscrizione non trovata!', 'danger')
        return redirect(url_for('iscrizioni.lista_iscrizioni'))

    if not iscrizione.test_superato or iscrizione.ore_frequentate < iscrizione.corso.ore_totali * 0.8:
        flash('Errore: Il discente non soddisfa i requisiti per l’attestato.', 'danger')
        return redirect(url_for('iscrizioni.lista_iscrizioni'))

    discente = iscrizione.discente
    corso = iscrizione.corso

    filename = f"{discente.cognome}_{discente.nome}_attestato.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)

    c = canvas.Canvas(filepath)
    c.drawString(100, 750, f"Attestato di Partecipazione")
    c.drawString(100, 730, f"Certifica che {discente.nome} {discente.cognome}")
    c.drawString(100, 710, f"Ha completato il corso '{corso.nome}' con {iscrizione.ore_frequentate} ore")
    c.drawString(100, 690, f"Punteggio test: {iscrizione.punteggio_test}%")
    c.save()

    flash('Attestato generato con successo!', 'success')
    return send_file(filepath, as_attachment=True)
