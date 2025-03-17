from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app.models.models import db, Corso, Progetto, Iscrizione

corsi_bp = Blueprint('corsi', __name__, url_prefix='/corsi')

# 📌 Configurazione cartelle di upload
UPLOAD_FOLDER = "static/uploads/tests"
UPLOAD_FOLDER_POST = "static/uploads/tests_post"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# ✅ Funzione per verificare se il file è di un tipo consentito
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 📌 Rotta per visualizzare tutti i corsi (con login richiesto)
@corsi_bp.route('/')
@login_required
def lista_corsi():
    print(f"DEBUG: Utente corrente -> {current_user}")  # 👀 Debug per verificare current_user
    corsi = Corso.query.all()
    progetti = Progetto.query.all()

    # Modifica: recupera i discenti iscritti per ciascun corso
    iscrizioni_per_corso = {}
    for corso in corsi:
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
        iscrizioni_per_corso[corso.id] = iscrizioni

    return render_template('corsi.html', corsi=corsi, progetti=progetti, iscrizioni_per_corso=iscrizioni_per_corso)

# 📌 Rotta per caricare i test iniziale, finale e post-corso
@corsi_bp.route('/<int:corso_id>/upload_test', methods=['POST'])
@login_required
def upload_test(corso_id):
    corso = Corso.query.get_or_404(corso_id)

    file_iniziale = request.files.get('test_iniziale')
    file_finale = request.files.get('test_finale')

    if not file_iniziale or not file_finale:
        flash("Devi selezionare entrambi i file!", "danger")
        return redirect(url_for('corsi.lista_corsi'))

    if file_iniziale and allowed_file(file_iniziale.filename):
        filename_iniziale = secure_filename(file_iniziale.filename)
        path_iniziale = os.path.join(UPLOAD_FOLDER, filename_iniziale)
        file_iniziale.save(path_iniziale)
        corso.test_iniziale = filename_iniziale

    if file_finale and allowed_file(file_finale.filename):
        filename_finale = secure_filename(file_finale.filename)
        path_finale = os.path.join(UPLOAD_FOLDER, filename_finale)
        file_finale.save(path_finale)
        corso.test_finale = filename_finale

    db.session.commit()
    flash("Test iniziale e finale caricati con successo!", "success")
    return redirect(url_for('corsi.lista_corsi'))

# 📌 Rotta per il caricamento del Test Post-Corso
@corsi_bp.route('/<int:corso_id>/upload_test_post', methods=['POST'])
@login_required
def upload_test_post(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    file_postcorso = request.files.get('test_postcorso')

    if not file_postcorso or not allowed_file(file_postcorso.filename):
        flash("Formato non valido! Carica un file PDF, DOC o DOCX.", "danger")
        return redirect(url_for('corsi.lista_corsi'))

    filename_postcorso = secure_filename(file_postcorso.filename)
    path_postcorso = os.path.join(UPLOAD_FOLDER_POST, filename_postcorso)
    file_postcorso.save(path_postcorso)
    corso.test_postcorso = filename_postcorso

    db.session.commit()
    flash("Test post-corso caricato con successo!", "success")
    return redirect(url_for('corsi.lista_corsi'))

# 📌 Rotta per aggiungere un nuovo corso
@corsi_bp.route('/aggiungi', methods=['POST'])
@login_required
def aggiungi_corso():
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')
    docente = request.form.get('docente')
    ore_totali = request.form.get('ore_totali')
    progetto_id = request.form.get('progetto_id')

    if not nome or not docente or not ore_totali or not progetto_id:
        flash("Tutti i campi sono obbligatori!", "danger")
        return redirect(url_for('corsi.lista_corsi'))

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

# 📌 Rotta per modificare un corso
@corsi_bp.route('/modifica/<int:id>', methods=['GET', 'POST'])
@login_required
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
@login_required
def elimina_corso(id):
    corso = Corso.query.get_or_404(id)
    Iscrizione.query.filter_by(corso_id=id).delete()
    db.session.delete(corso)
    db.session.commit()
    flash('Corso eliminato con successo!', 'success')
    return redirect(url_for('corsi.lista_corsi'))