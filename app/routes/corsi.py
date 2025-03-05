from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Corso, Progetto, Iscrizione

corsi_bp = Blueprint('corsi', __name__, url_prefix='/corsi')

@corsi_bp.route('/')
def lista_corsi():
    corsi = Corso.query.all()
    progetti = Progetto.query.all()  # Recuperiamo i progetti per la selezione
    return render_template('corsi.html', corsi=corsi, progetti=progetti)

@corsi_bp.route('/aggiungi', methods=['POST'])
def aggiungi_corso():
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')  # Assicurati che venga acquisito correttamente
    docente = request.form.get('docente')
    ore_totali = request.form.get('ore_totali')
    progetto_id = request.form.get('progetto_id')

    if nome and docente and ore_totali and progetto_id:
        nuovo_corso = Corso(
            nome=nome,
            descrizione=descrizione,  # Deve esistere nel modello
            docente=docente,
            ore_totali=int(ore_totali),
            progetto_id=int(progetto_id)
        )

        db.session.add(nuovo_corso)
        db.session.commit()
        flash("Corso aggiunto con successo!", "success")

    return redirect(url_for('corsi.lista_corsi'))

@corsi_bp.route('/elimina/<int:id>', methods=['POST'])
def elimina_corso(id):
    corso = Corso.query.get(id)
    if corso:
        # Eliminare tutte le iscrizioni associate a questo corso
        Iscrizione.query.filter_by(corso_id=id).delete()
        
        # Eliminare il corso
        db.session.delete(corso)
        db.session.commit()
        flash('Corso eliminato con successo!', 'success')

    return redirect(url_for('corsi.lista_corsi'))
