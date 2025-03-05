from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Iscrizione, Discente, Corso

iscrizioni_bp = Blueprint('iscrizioni', __name__)

@iscrizioni_bp.route('/')
def lista_iscrizioni():
    iscrizioni = Iscrizione.query.all()
    discenti = Discente.query.all()
    corsi = Corso.query.all()

    return render_template('iscrizioni.html', iscrizioni=iscrizioni, discenti=discenti, corsi=corsi)

@iscrizioni_bp.route('/assegna', methods=['POST'])
def assegna_discente():
    discente_id = request.form.get('discente_id')
    corso_id = request.form.get('corso_id')

    if not discente_id or not corso_id:
        flash('Seleziona sia un discente che un corso!', 'danger')
        return redirect(url_for('iscrizioni.lista_iscrizioni'))

    # Verifica se il discente è già iscritto al corso
    esiste_iscrizione = Iscrizione.query.filter_by(discente_id=discente_id, corso_id=corso_id).first()
    if esiste_iscrizione:
        flash('Questo discente è già iscritto a questo corso!', 'warning')
        return redirect(url_for('iscrizioni.lista_iscrizioni'))

    nuova_iscrizione = Iscrizione(discente_id=discente_id, corso_id=corso_id)
    db.session.add(nuova_iscrizione)
    db.session.commit()

    flash('Discente assegnato con successo al corso!', 'success')
    return redirect(url_for('iscrizioni.lista_iscrizioni'))
