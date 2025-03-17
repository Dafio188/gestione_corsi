# routes/progetti.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.models.models import Progetto
from datetime import datetime

# Definizione del Blueprint per i progetti
progetti_bp = Blueprint('progetti', __name__, url_prefix='/progetti')

@progetti_bp.route('/')
def lista_progetti():
    """
    Mostra l'elenco dei progetti con il numero di discenti associati.
    """
    # Recupera tutti i progetti dal database
    progetti = Progetto.query.all()

    # Calcola il numero di discenti per ciascun progetto
    for progetto in progetti:
        progetto.numero_discenti = len(progetto.discenti)  # Usa la relazione "discenti" definita nel modello

    return render_template('progetti.html', progetti=progetti)

@progetti_bp.route('/aggiungi', methods=['POST'])
def aggiungi_progetto():
    """
    Aggiunge un nuovo progetto al database.
    """
    # Recupera i dati dal form
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')
    ente = request.form.get('ente')
    inizio_progetto = request.form.get('inizio_progetto')
    fine_progetto = request.form.get('fine_progetto')

    # Conversione delle date (gestisce anche il caso di valori vuoti)
    inizio_progetto = datetime.strptime(inizio_progetto, '%Y-%m-%d').date() if inizio_progetto else None
    fine_progetto = datetime.strptime(fine_progetto, '%Y-%m-%d').date() if fine_progetto else None

    # Crea un nuovo progetto e lo aggiunge al database
    if nome:
        nuovo_progetto = Progetto(
            nome=nome,
            descrizione=descrizione,
            ente=ente,
            inizio_progetto=inizio_progetto,
            fine_progetto=fine_progetto
        )
        db.session.add(nuovo_progetto)
        db.session.commit()
        flash("Progetto aggiunto con successo!", "success")
    else:
        flash("Il campo 'Nome Progetto' è obbligatorio.", "danger")

    return redirect(url_for('progetti.lista_progetti'))

@progetti_bp.route('/elimina/<int:progetto_id>', methods=['POST'])
def elimina_progetto(progetto_id):
    """
    Elimina un progetto dal database.
    """
    # Recupera il progetto dal database
    progetto = Progetto.query.get_or_404(progetto_id)

    # Elimina il progetto
    db.session.delete(progetto)
    db.session.commit()

    flash(f"Il progetto '{progetto.nome}' è stato eliminato con successo.", "success")
    return redirect(url_for('progetti.lista_progetti'))