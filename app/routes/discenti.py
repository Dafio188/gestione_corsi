from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Discente, Corso, Progetto, Iscrizione
import random
import string
from werkzeug.security import generate_password_hash
import pandas as pd
from werkzeug.utils import secure_filename

discenti_bp = Blueprint('discenti', __name__, url_prefix='/discenti')

@discenti_bp.route('/')
def lista_discenti():
    # Recupera tutti i discenti dal database
    discenti = Discente.query.all()

    # Recupera tutti i progetti dal database
    progetti = Progetto.query.all()

    # Aggiunge la lista dei corsi direttamente all'oggetto Discente
    for discente in discenti:
        discente.corsi = [iscrizione.corso.nome for iscrizione in discente.iscrizioni]

    return render_template('discenti.html', discenti=discenti, progetti=progetti)

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
            # 🔹 Generiamo una password temporanea
            password_temporanea = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            password_hash = generate_password_hash(password_temporanea)

            nuovo_discente = Discente(
                nome=nome,
                cognome=cognome,
                codice_fiscale=codice_fiscale,
                genere=genere,
                fascia_eta=fascia_eta,
                ruolo=ruolo,
                email=email,
                password_hash=password_hash,  # ✅ Salviamo la password criptata
                cellulare=cellulare,
                progetto_id=int(progetto_id)
            )

            db.session.add(nuovo_discente)
            db.session.commit()

            for corso_id in corsi_ids:
                iscrizione = Iscrizione(discente_id=nuovo_discente.id, corso_id=int(corso_id))
                db.session.add(iscrizione)

            db.session.commit()

            # ✅ Mostriamo la password temporanea all'amministratore
            flash(f"Discente aggiunto con successo! La password temporanea è: {password_temporanea}", "success")

            return redirect(url_for('discenti.lista_discenti'))

    corsi = Corso.query.all()
    progetti = Progetto.query.all()
    return render_template('aggiungi_discente.html', corsi=corsi, progetti=progetti)

@discenti_bp.route('/importa', methods=['POST'])
def importa_discenti():
    if 'excelFile' not in request.files:
        flash('Nessun file selezionato', 'danger')
        return redirect(url_for('discenti.lista_discenti'))

    file = request.files['excelFile']

    if file.filename == '':
        flash('Nessun file selezionato', 'danger')
        return redirect(url_for('discenti.lista_discenti'))

    if file:
        try:
            # Leggi il file Excel con pandas
            df = pd.read_excel(file)

            # Split 'Inserisci il tuo Nome e Cognome' into 'nome' and 'cognome'
            def split_nome_cognome(row):
                nome_cognome = row['Inserisci il tuo Nome e Cognome']
                split_result = nome_cognome.split(' ', 1)  # Split only once

                if len(split_result) == 2:
                    return split_result[0], split_result[1]
                elif len(split_result) == 1:
                    return split_result[0], 'Unknown'  # If only one element, assign it to nome and 'Unknown' to cognome
                else:
                    return 'Unknown', 'Unknown'  # If empty or other unexpected format

            df['nome'], df['cognome'] = zip(*df.apply(split_nome_cognome, axis=1))

            # Assign the `progetto_id` column with the `Indicare la tua età` column
            df['progetto_id'] = df['Indicare la tua età']

            # Generate a temporary 'codice_fiscale'
            df['codice_fiscale'] = [''.join(random.choices(string.ascii_uppercase + string.digits, k=16)) for _ in range(len(df))]

            # Rename `Email` column to `email`
            df = df.rename(columns={'Email': 'email'})

            # Crea un nuovo dataframe con le colonne richieste
            df = df[['nome', 'cognome', 'email', 'progetto_id', 'codice_fiscale']].copy()

            # Itera attraverso le righe del file Excel
            for index, row in df.iterrows():
                # Estrai i dati dalla riga
                nome = row['nome']
                cognome = row['cognome']
                codice_fiscale = row['codice_fiscale']
                email = row['email']
                progetto_id = row['progetto_id']

                # Verifica che i dati siano validi
                if not all([nome, cognome, codice_fiscale, email, progetto_id]):
                    flash(f'Dati mancanti alla riga {index + 2}', 'danger')
                    return redirect(url_for('discenti.lista_discenti'))

                # Genera una password temporanea
                password_temporanea = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                password_hash = generate_password_hash(password_temporanea)

                # Crea un nuovo discente
                nuovo_discente = Discente(
                    nome=nome,
                    cognome=cognome,
                    codice_fiscale=codice_fiscale,
                    email=email,
                    password_hash=password_hash,
                    progetto_id=progetto_id
                )

                # Aggiungi il discente al database
                db.session.add(nuovo_discente)

            # Salva le modifiche al database
            db.session.commit()

            flash('Discenti importati con successo!', 'success')
        except Exception as e:
            flash(f'Errore durante l\'importazione: {str(e)}', 'danger')

    return redirect(url_for('discenti.lista_discenti'))