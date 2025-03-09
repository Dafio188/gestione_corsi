from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.models.models import Corso, TestRisultato, Discente

test_bp = Blueprint('test', __name__)

# ✅ LISTA DEI TEST DISPONIBILI
@test_bp.route('/')
def lista_test():
    corsi = Corso.query.all()
    discenti = Discente.query.all()  # ✅ Aggiunto per il form di valutazione
    return render_template('test.html', corsi=corsi, discenti=discenti)

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

# ✅ COMPILA UN TEST POST-CORSO (sezione già esistente)
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
        
        superato = punteggio >= 60  # Soglia di superamento del test

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

# ✅ NUOVA ROUTE PER VALUTARE IL TEST (mancava prima)
@test_bp.route('/valuta_test', methods=['POST'])
def valuta_test():
    print("DEBUG: Endpoint valuta_test chiamato correttamente")  # <-- Debug per test
    corso_id = request.form.get('corso_id')
    discente_id = request.form.get('discente_id')
    punteggio = request.form.get('punteggio')

    if not corso_id or not discente_id or not punteggio:
        flash("Errore: Assicurati di aver inserito tutte le informazioni.", "danger")
        return redirect(url_for('test.lista_test'))

    try:
        punteggio = int(punteggio)
    except ValueError:
        flash("Errore: Il punteggio deve essere un numero.", "danger")
        return redirect(url_for('test.lista_test'))

    superato = punteggio >= 60  # Soglia di superamento del test

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
