from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Iscrizione, Discente, Corso

iscrizioni_bp = Blueprint('iscrizioni', __name__, url_prefix='/iscrizioni')

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
        flash("Errore: Assicurati di selezionare un discente e un corso.", "danger")
        return redirect(url_for('iscrizioni.lista_iscrizioni'))

    nuova_iscrizione = Iscrizione(discente_id=int(discente_id), corso_id=int(corso_id))
    db.session.add(nuova_iscrizione)
    db.session.commit()

    flash("Discente assegnato al corso con successo!", "success")
    return redirect(url_for('iscrizioni.lista_iscrizioni'))

# ✅ **ROUTE PER ELIMINARE UN'ISCRIZIONE (Correggi il nome)**
@iscrizioni_bp.route('/elimina/<int:iscrizione_id>', methods=['POST'])
def elimina_iscrizione(iscrizione_id):
    iscrizione = Iscrizione.query.get(iscrizione_id)
    if iscrizione:
        db.session.delete(iscrizione)
        db.session.commit()
        flash("Iscrizione eliminata con successo!", "success")
    else:
        flash("Errore: Iscrizione non trovata.", "danger")

    return redirect(url_for('iscrizioni.lista_iscrizioni'))
