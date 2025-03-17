from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from flask_login import login_required
from app.models.models import Corso, TestRisultato, Discente, Iscrizione

test_bp = Blueprint('test', __name__)

# 🔹 Gestione Test (Mostra il modulo con i dati del discente)
@test_bp.route('/gestione_test/<int:corso_id>/<int:discente_id>')
@login_required
def gestione_test(corso_id, discente_id):
    iscrizione = Iscrizione.query.filter_by(corso_id=corso_id, discente_id=discente_id).first()
    if iscrizione is None:
        flash('Iscrizione non trovata.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('test.html', iscrizione=iscrizione)

# ✅ LISTA DEI TEST DISPONIBILI
@test_bp.route('/')
def lista_test():
    corsi = Corso.query.all()
    discenti = Discente.query.all()
    iscrizioni = {i.discente_id: i.ore_frequentate for i in Iscrizione.query.all()}  # ✅ Recupera ore frequentate
    return render_template('test.html', corsi=corsi, discenti=discenti, iscrizioni=iscrizioni)

# ✅ CARICA UN TEST (già esistente, ma lo manteniamo)
@test_bp.route('/carica_test', methods=['POST'])
def carica_test():
    corso_id = request.form.get('corso_id')
    test_file = request.files.get('test_file')

    if not corso_id or not test_file:
        flash("Errore: Assicurati di aver selezionato un corso e un file per il test.", "danger")
        return redirect(url_for('test.lista_test'))

    # Salvataggio del file test (modifica in base alla tua logica)
    test_path = f"uploads/test/{test_file.filename}"
    test_file.save(test_path)

    corso = Corso.query.get(corso_id)
    if corso:
        corso.test_preliminare = test_path  # Se il file è per il test preliminare
        db.session.commit()
        flash("Test caricato con successo!", "success")
    else:
        flash("Errore: Corso non trovato.", "danger")

    return redirect(url_for('test.lista_test'))

# ✅ COMPILA UN TEST POST-CORSO
@test_bp.route('/compila_test_post/<int:corso_id>/<int:discente_id>', methods=['GET', 'POST'])
def compila_test_post(corso_id, discente_id):
    corso = Corso.query.get_or_404(corso_id)
    discente = Discente.query.get_or_404(discente_id)

    if request.method == 'POST':
        try:
            punteggio = int(request.form.get('punteggio', 0))
        except ValueError:
            flash("Errore: Il punteggio deve essere un numero.", "danger")
            return redirect(url_for('test.lista_test'))
        
        superato = punteggio >= 85  # Soglia di superamento del test

        nuovo_test = TestRisultato(
            discente_id=discente.id,
            corso_id=corso.id,
            punteggio_ottenuto=punteggio,
            superato=superato
        )

        db.session.add(nuovo_test)
        db.session.commit()

        flash("Test compilato con successo!", "success")
        return redirect(url_for('test.lista_test'))

    return render_template('compila_test_post.html', corso=corso, discente=discente)

@test_bp.route('/valuta_test', methods=['POST'])
@login_required
def valuta_test():
    corso_id = request.form.get('corso_id')
    discente_id = request.form.get('discente_id')
    punteggio = request.form.get('punteggio')
    ore_frequentate = request.form.get('ore_frequentate')

    if not corso_id or not discente_id or not punteggio or not ore_frequentate:
        flash("Errore: Assicurati di aver inserito tutte le informazioni.", "danger")
        return redirect(url_for('test.lista_test'))

    try:
        punteggio = int(punteggio)
        ore_frequentate = int(ore_frequentate)
    except ValueError:
        flash("Errore: Il punteggio e le ore frequentate devono essere numeri.", "danger")
        return redirect(url_for('test.lista_test'))

    # ✅ Recupera il corso per ottenere il numero totale di ore
    corso = Corso.query.get(int(corso_id))
    if not corso:
        flash("Errore: Corso non trovato.", "danger")
        return redirect(url_for('test.lista_test'))

    # ✅ Calcola la soglia minima delle ore (80% delle ore totali del corso)
    ore_minime = int(corso.ore_totali * 0.8)  

    # ✅ Controllo superamento test con numero di ore effettive
    superato = punteggio >= 85 and ore_frequentate >= ore_minime

    # ✅ Aggiorna la tabella Iscrizione
    iscrizione = Iscrizione.query.filter_by(discente_id=int(discente_id), corso_id=int(corso_id)).first()
    if iscrizione:
        iscrizione.test_superato = superato  # ✅ Segna il test come superato solo se ha i requisiti
        iscrizione.punteggio_test = punteggio
        iscrizione.ore_frequentate = ore_frequentate
        db.session.commit()
        flash("Test valutato con successo!", "success")
    else:
        flash("Errore: Iscrizione non trovata.", "danger")

    return redirect(url_for('test.lista_test'))


    # ✅ CREA UN NUOVO RISULTATO NELLA TABELLA TestRisultato
    nuovo_risultato = TestRisultato(
        discente_id=int(discente_id),
        corso_id=int(corso_id),
        punteggio_ottenuto=punteggio,
        superato=superato
    )

    db.session.add(nuovo_risultato)
    db.session.commit()

    flash("Test valutato con successo!", "success")
    return redirect(url_for('test.lista_test'))

    # ✅ Aggiorna anche la tabella Iscrizione
    iscrizione = Iscrizione.query.filter_by(discente_id=int(discente_id), corso_id=int(corso_id)).first()
    if iscrizione:
        iscrizione.test_superato = superato
        iscrizione.punteggio_test = punteggio
        iscrizione.ore_frequentate = ore_frequentate  # ✅ Salva il valore aggiornato

    db.session.commit()

    flash("Test valutato con successo!", "success")
    return redirect(url_for('test.lista_test'))

