from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.models.models import Progetto
from datetime import datetime

progetti_bp = Blueprint('progetti', __name__, url_prefix='/progetti')

@progetti_bp.route('/')
def lista_progetti():
    progetti = Progetto.query.all()
    return render_template('progetti.html', progetti=progetti)

@progetti_bp.route('/aggiungi', methods=['POST'])
def aggiungi_progetto():
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')
    ente = request.form.get('ente')
    inizio_progetto = request.form.get('inizio_progetto')
    fine_progetto = request.form.get('fine_progetto')

    # Conversione delle date (gestisce anche il caso di valori vuoti)
    inizio_progetto = datetime.strptime(inizio_progetto, '%Y-%m-%d').date() if inizio_progetto else None
    fine_progetto = datetime.strptime(fine_progetto, '%Y-%m-%d').date() if fine_progetto else None

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

    return redirect(url_for('progetti.lista_progetti'))
