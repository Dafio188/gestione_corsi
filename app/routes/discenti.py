from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Discente, Corso, Progetto, Iscrizione

discenti_bp = Blueprint('discenti', __name__, url_prefix='/discenti')

@discenti_bp.route('/')
def lista_discenti():
    discenti = Discente.query.all()
    return render_template('discenti.html', discenti=discenti)

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
        corsi_ids = request.form.getlist('corsi_ids')  # Ottiene una lista di ID corsi selezionati

        if nome and cognome and codice_fiscale and email and progetto_id:
            nuovo_discente = Discente(
                nome=nome,
                cognome=cognome,
                codice_fiscale=codice_fiscale,
                genere=genere,
                fascia_eta=fascia_eta,
                ruolo=ruolo,
                email=email,
                cellulare=cellulare,
                progetto_id=int(progetto_id)  # Assegna il discente al progetto
            )
            db.session.add(nuovo_discente)
            db.session.commit()

            # Assegnazione corsi selezionati
            for corso_id in corsi_ids:
                iscrizione = Iscrizione(discente_id=nuovo_discente.id, corso_id=int(corso_id))
                db.session.add(iscrizione)

            db.session.commit()
            flash("Discente aggiunto con successo!", "success")
            return redirect(url_for('discenti.lista_discenti'))

    # Se GET, mostra il form con i progetti e corsi
    corsi = Corso.query.all()
    progetti = Progetto.query.all()
    return render_template('aggiungi_discente.html', corsi=corsi, progetti=progetti)

@discenti_bp.route('/elimina/<int:id>', methods=['POST'])
def elimina_discente(id):
    discente = Discente.query.get(id)
    if discente:
        # Elimina tutte le iscrizioni associate
        Iscrizione.query.filter_by(discente_id=id).delete()

        # Elimina il discente
        db.session.delete(discente)
        db.session.commit()
        flash('Discente eliminato con successo!', 'success')

    return redirect(url_for('discenti.lista_discenti'))
