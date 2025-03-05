from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Lezione, Presenza, Discente, Corso
from datetime import datetime

presenze_bp = Blueprint('presenze', __name__)

@presenze_bp.route('/')
def lista_presenze():
    corsi = Corso.query.all()
    lezioni = Lezione.query.all()
    return render_template('presenze.html', corsi=corsi, lezioni=lezioni)

@presenze_bp.route('/aggiungi_lezione', methods=['POST'])
def aggiungi_lezione():
    corso_id = request.form.get('corso_id')
    data_lezione = request.form.get('data_lezione')
    orario = request.form.get('orario')

    if not corso_id or not data_lezione or not orario:
        flash('Tutti i campi sono obbligatori!', 'danger')
        return redirect(url_for('presenze.lista_presenze'))

    nuova_lezione = Lezione(
        corso_id=corso_id,
        data_lezione=datetime.strptime(data_lezione, "%Y-%m-%d").date(),
        orario=orario
    )

    db.session.add(nuova_lezione)
    db.session.commit()

    flash('Lezione aggiunta con successo!', 'success')
    return redirect(url_for('presenze.lista_presenze'))

@presenze_bp.route('/registra_presenza', methods=['POST'])
def registra_presenza():
    lezione_id = request.form.get('lezione_id')
    discente_id = request.form.get('discente_id')

    if not lezione_id or not discente_id:
        flash('Seleziona una lezione e un discente!', 'danger')
        return redirect(url_for('presenze.lista_presenze'))

    nuova_presenza = Presenza(lezione_id=lezione_id, discente_id=discente_id, presente=True)
    db.session.add(nuova_presenza)
    db.session.commit()

    flash('Presenza registrata con successo!', 'success')
    return redirect(url_for('presenze.lista_presenze'))
