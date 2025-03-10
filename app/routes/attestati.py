import os
from flask import Blueprint, request, redirect, url_for, flash, send_file, render_template
from flask_login import login_required
from app.models.models import db, Iscrizione, Discente, Corso
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

attestati_bp = Blueprint('attestati', __name__)

@attestati_bp.route('/lista')
@login_required
def lista_attestati():
    iscrizioni = Iscrizione.query.all()  # Recupera tutte le iscrizioni
    return render_template('lista_attestati.html', iscrizioni=iscrizioni)

# ✅ GENERA ATTESTATO PDF
@attestati_bp.route('/genera_attestato/<int:corso_id>/<int:discente_id>')
@login_required
def genera_attestato(corso_id, discente_id):
    iscrizione = Iscrizione.query.filter_by(corso_id=corso_id, discente_id=discente_id).first()
    
    if not iscrizione or not iscrizione.puo_ricevere_attestato():
        flash("Errore: Questo discente non soddisfa i requisiti per l'attestato.", "danger")
        return redirect(url_for('test.lista_test'))

    discente = Discente.query.get(discente_id)
    corso = Corso.query.get(corso_id)

    base_dir = os.path.join(os.getcwd(), "app", "static", "attestati")
    os.makedirs(base_dir, exist_ok=True)

    filename = f"{discente.nome}_{discente.cognome}_attestato.pdf"
    filepath = os.path.join(base_dir, filename)

    sfondo_path = os.path.join(os.getcwd(), "app", "static", "img", "attestato_sfondo.png")
    if not os.path.exists(sfondo_path):
        flash("Errore: Il file dello sfondo non è stato trovato.", "danger")
        return redirect(url_for('test.lista_test'))

    # ✅ Impostazioni del PDF
    page_width, page_height = A4
    c = canvas.Canvas(filepath, pagesize=A4)
    c.drawImage(ImageReader(sfondo_path), 0, 0, width=page_width, height=page_height)  # Sfondo a tutta pagina

    # ✅ Registra un font calligrafico
    font_path = os.path.join(os.getcwd(), "app", "static", "fonts", "GreatVibes-Regular.ttf")  # Assicurati che esista!
    pdfmetrics.registerFont(TTFont('Calligrafico', font_path))

    # ✅ Impostazioni font e colore del testo
    c.setFont("Calligrafico", 40)  # Nome più grande per evidenziarlo
    c.setFillColorRGB(0, 0, 0)  # Testo in nero

    # 📌 Nome del discente (SCESO DI 4 RIGHE)
    text_x = (page_width / 2) - 90  # Spostato leggermente a destra
    c.drawString(text_x, 500, f"{discente.nome} {discente.cognome}")  # Prima era 600, ora 500 (abbassato di 100px)

    # 📌 Nome del corso (SCESO DI 4 RIGHE)
    c.setFont("Calligrafico", 24)
    c.drawString(text_x - 20, 450, f"Ha frequentato il corso: {corso.nome}")

    # 📌 Ore frequentate (SCESO DI 4 RIGHE)
    c.setFont("Calligrafico", 22)
    c.drawString(text_x, 410, f"Ore Frequentate: {iscrizione.ore_frequentate} / {corso.ore_totali}")

    # 📌 Punteggio test (SCESO DI 4 RIGHE)
    c.drawString(text_x, 370, f"Punteggio Test: {iscrizione.punteggio_test}%")

    # 📌 Firma o timbro (in basso a destra)
    c.setFont("Helvetica-Oblique", 14)
    c.drawString(page_width - 200, 100, "Firma e Timbro")

    c.showPage()
    c.save()

    flash("Attestato generato con successo!", "success")
    return send_file(filepath, as_attachment=True)
