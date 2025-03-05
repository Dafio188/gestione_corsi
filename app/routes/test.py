import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.models.models import db, Corso

test_bp = Blueprint('test', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# Assicurati che la cartella di upload esista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@test_bp.route('/')
def lista_test():
    corsi = Corso.query.all()
    return render_template('test.html', corsi=corsi)

@test_bp.route('/carica_test', methods=['POST'])
def carica_test():
    corso_id = request.form.get('corso_id')
    file = request.files.get('file')

    if not corso_id or not file:
        flash('Seleziona un corso e un file!', 'danger')
        return redirect(url_for('test.lista_test'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        flash('Test caricato con successo!', 'success')
    else:
        flash('Formato file non valido!', 'danger')

    return redirect(url_for('test.lista_test'))

@test_bp.route('/valuta_test', methods=['POST'])
def valuta_test():
    corso_id = request.form.get('corso_id')
    punteggio = request.form.get('punteggio')

    if not corso_id or not punteggio:
        flash('Seleziona un corso e inserisci un punteggio!', 'danger')
        return redirect(url_for('test.lista_test'))

    flash(f'Test valutato con punteggio {punteggio}!', 'success')
    return redirect(url_for('test.lista_test'))
