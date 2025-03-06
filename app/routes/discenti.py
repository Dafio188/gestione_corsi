from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Discente, Corso, Progetto, Iscrizione

discenti_bp = Blueprint('discenti', __name__, url_prefix='/discenti')

@discenti_bp.route('/')
def lista_discenti():
    discenti = Discente.query.all()

    # Aggiunge la lista dei corsi direttamente all'oggetto Discente
    for discente in discenti:
        discente.corsi = [iscrizione.corso.nome for iscrizione in discente.iscrizioni] 

    return render_template('discenti.html', discenti=discenti)

@discenti_bp.route('/elimina/<int:id>', methods=['POST'])
def elimina_discente(id):
    discente = Discente.query.get(id)
    if discente:
        Iscrizione.query.filter_by(discente_id=id).delete()  # Elimina iscrizioni
        db.session.delete(discente)  # Elimina discente
        db.session.commit()
        flash('Discente eliminato con successo!', 'success')
    return redirect(url_for('discenti.lista_discenti'))

@discenti_bp.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica_discente(id):
    discente = Discente.query.get_or_404(id)
    corsi = Corso.query.all()
    progetti = Progetto.query.all()

    if request.method == 'POST':
        discente.nome = request.form.get('nome')
        discente.cognome = request.form.get('cognome')
        discente.codice_fiscale = request.form.get('codice_fiscale')
        discente.genere = request.form.get('genere')
        discente.fascia_eta = request.form.get('fascia_eta')
        discente.ruolo = request.form.get('ruolo')
        discente.email = request.form.get('email')
        discente.cellulare = request.form.get('cellulare')
        discente.progetto_id = request.form.get('progetto_id')

        # 🔹 Aggiorniamo le iscrizioni ai corsi: prima rimuoviamo quelle esistenti
        Iscrizione.query.filter_by(discente_id=id).delete()

        # 🔹 Ora aggiungiamo le nuove iscrizioni selezionate dall'utente
        corsi_ids = request.form.getlist('corsi_ids')
        for corso_id in corsi_ids:
            iscrizione = Iscrizione(discente_id=id, corso_id=int(corso_id))
            db.session.add(iscrizione)

        db.session.commit()
        flash("Discente modificato con successo!", "success")
        return redirect(url_for('discenti.lista_discenti'))

    return render_template('modifica_discente.html', discente=discente, corsi=corsi, progetti=progetti)

@discenti_bp.route('/aggiungi', methods=['GET', 'POST'])
def aggiungi_discente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        codice_fiscale = request.form.get('codice_fiscale')
        genere = request.form.get('genere')
        fascia_eta = request.form.get('fascia_eta')
        ruolo = request.form.get('ruolo')
        email = request.form.get('email')
        cellulare = request.form.get('cellulare')
        progetto_id = request.form.get('progetto_id')
        corsi_ids = request.form.getlist('corsi_ids')

        if nome and cognome and codice_fiscale and email and progetto_id:
            nuovo_discente = Discente(
                nome=nome, cognome=cognome, codice_fiscale=codice_fiscale,
                genere=genere, fascia_eta=fascia_eta, ruolo=ruolo,
                email=email, cellulare=cellulare, progetto_id=int(progetto_id)
            )
            db.session.add(nuovo_discente)
            db.session.commit()

            for corso_id in corsi_ids:
                iscrizione = Iscrizione(discente_id=nuovo_discente.id, corso_id=int(corso_id))
                db.session.add(iscrizione)

            db.session.commit()
            flash("Discente aggiunto con successo!", "success")
            return redirect(url_for('discenti.lista_discenti'))

    corsi = Corso.query.all()
    progetti = Progetto.query.all()
    return render_template('aggiungi_discente.html', corsi=corsi, progetti=progetti)
