from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Iscrizione, Discente, Corso

ore_frequentate_bp = Blueprint('ore_frequentate', __name__)

@ore_frequentate_bp.route('/')
def lista_frequenze():
    iscrizioni = Iscrizione.query.all()
    return render_template('ore_frequentate.html', iscrizioni=iscrizioni)

@ore_frequentate_bp.route('/aggiorna', methods=['POST'])
def aggiorna_ore():
    iscrizione_id = request.form.get('iscrizione_id')
    ore_aggiunte = int(request.form.get('ore_aggiunte'))

    iscrizione = Iscrizione.query.get(iscrizione_id)
    if iscrizione:
        iscrizione.ore_frequentate += ore_aggiunte
        db.session.commit()
        flash(f'Ore aggiornate! Ora il discente ha frequentato {iscrizione.ore_frequentate} ore.', 'success')
    else:
        flash('Errore: iscrizione non trovata!', 'danger')

    return redirect(url_for('ore_frequentate.lista_frequenze'))
