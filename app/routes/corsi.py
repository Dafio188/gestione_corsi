from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from app.models.models import db, Corso, Progetto, Iscrizione

corsi_bp = Blueprint('corsi', __name__, url_prefix='/corsi')

# Configurazione cartella di upload
UPLOAD_FOLDER = "static/uploads/tests"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Funzione per verificare se il file è di un tipo consentito
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 📌 Rotta per visualizzare tutti i corsi
@corsi_bp.route('/')
def lista_corsi():
    corsi = Corso.query.all()
    progetti = Progetto.query.all()  # Recupera i progetti per la selezione
    return render_template('corsi.html', corsi=corsi, progetti=progetti)

# 📌 Rotta per caricare i test iniziale e finale di un corso
@corsi_bp.route('/<int:corso_id>/upload_test', methods=['POST'])
def upload_test(corso_id):
    corso = Corso.query.get_or_404(corso_id)

    if 'test_iniziale' not in request.files or 'test_finale' not in request.files:
        flash("Devi selezionare entrambi i file!", "danger")
        return redirect(url_for('corsi.lista_corsi'))

    file_iniziale = request.files['test_iniziale']
    file_finale = request.files['test_finale']

    if file_iniziale and allowed_file(file_iniziale.filename):
        filename_iniziale = secure_filename(file_iniziale.filename)
        path_iniziale = os.path.join(UPLOAD_FOLDER, filename_iniziale)
        file_iniziale.save(path_iniziale)
        corso.test_iniziale = path_iniziale

    if file_finale and allowed_file(file_finale.filename):
        filename_finale = secure_filename(file_finale.filename)
        path_finale = os.path.join(UPLOAD_FOLDER, filename_finale)
        file_finale.save(path_finale)
        corso.test_finale = path_finale

    db.session.commit()
    flash("Test caricati con successo!", "success")
    return redirect(url_for('corsi.lista_corsi'))

# 📌 Rotta per aggiungere un nuovo corso
@corsi_bp.route('/aggiungi', methods=['POST'])
def aggiungi_corso():
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')
    docente = request.form.get('docente')
    ore_totali = request.form.get('ore_totali')
    progetto_id = request.form.get('progetto_id')

    if nome and docente and ore_totali and progetto_id:
        nuovo_corso = Corso(
            nome=nome,
            descrizione=descrizione,
            docente=docente,
            ore_totali=int(ore_totali),
            progetto_id=int(progetto_id)
        )

        db.session.add(nuovo_corso)
        db.session.commit()
        flash("Corso aggiunto con successo!", "success")

    return redirect(url_for('corsi.lista_corsi'))

# 📌 Rotta per modificare un corso 🔹🔹🔹 **NUOVA MODIFICA** 🔹🔹🔹
@corsi_bp.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica_corso(id):
    corso = Corso.query.get_or_404(id)
    progetti = Progetto.query.all()

    if request.method == 'POST':
        corso.nome = request.form.get('nome')
        corso.descrizione = request.form.get('descrizione')
        corso.docente = request.form.get('docente')
        corso.ore_totali = request.form.get('ore_totali')
        corso.progetto_id = request.form.get('progetto_id')

        db.session.commit()
        flash("Corso modificato con successo!", "success")
        return redirect(url_for('corsi.lista_corsi'))

    return render_template('modifica_corso.html', corso=corso, progetti=progetti)

# 📌 Rotta per eliminare un corso
@corsi_bp.route('/elimina/<int:id>', methods=['POST'])
def elimina_corso(id):
    corso = Corso.query.get(id)
    if corso:
        Iscrizione.query.filter_by(corso_id=id).delete()
        db.session.delete(corso)
        db.session.commit()
        flash('Corso eliminato con successo!', 'success')

    return redirect(url_for('corsi.lista_corsi'))
