# routes/report.py
from flask import Blueprint, render_template, request, send_file, jsonify
from io import BytesIO
import pandas as pd
from app.models.models import Progetto, Corso, Discente, Iscrizione  # Importa i modelli necessari

# Definizione del Blueprint
report_bp = Blueprint('report', __name__, url_prefix='/report')

# Route per recuperare i corsi associati a un progetto
@report_bp.route('/get_corsi/<int:progetto_id>')
def get_corsi(progetto_id):
    corsi = Corso.query.filter_by(progetto_id=progetto_id).all()
    return jsonify([{'id': corso.id, 'nome': corso.nome} for corso in corsi])

@report_bp.route('/completo', methods=['GET', 'POST'])
def report_completo():
    # Recupera tutti i progetti per popolare il menu a tendina
    progetti = Progetto.query.all()
    corsi = []
    discenti_filtrati = []
    corso_selezionato = None
    progetto_selezionato = None
    filtro_attestato = None

    if request.method == 'POST':
        # Recupera i filtri dal form
        progetto_id = request.form.get('progetto_id')
        corso_id = request.form.get('corso_id')
        attestato = request.form.get('attestato')  # "Sì" o "No"

        # Filtra i corsi in base al progetto selezionato
        if progetto_id:
            progetto_selezionato = Progetto.query.get(progetto_id)
            corsi = Corso.query.filter_by(progetto_id=progetto_id).all()

        # Filtra i discenti in base al corso selezionato
        if corso_id:
            corso_selezionato = Corso.query.get(corso_id)
            iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()

            for iscrizione in iscrizioni:
                if attestato == "Sì" and iscrizione.puo_ricevere_attestato():
                    discenti_filtrati.append(iscrizione.discente)
                elif attestato == "No" and not iscrizione.puo_ricevere_attestato():
                    discenti_filtrati.append(iscrizione.discente)

        # Esportazione in Excel
        if request.form.get('azione') == 'esporta_excel':
            data = []
            for discente in discenti_filtrati:
                data.append({
                    'Nome': discente.nome,
                    'Cognome': discente.cognome,
                    'Email': discente.email,
                    'Corso': corso_selezionato.nome if corso_selezionato else "N/A",
                    'Progetto': progetto_selezionato.nome if progetto_selezionato else "N/A",
                    'Attestato Rilasciato': 'Sì' if attestato == "Sì" else 'No'
                })

            # Crea un DataFrame pandas
            df = pd.DataFrame(data)

            # Genera il file Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            output.seek(0)

            # Restituisci il file come download
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='report.xlsx'
            )

    return render_template(
        'report_completo.html',
        progetti=progetti,
        corsi=corsi,
        discenti_filtrati=discenti_filtrati,
        corso_selezionato=corso_selezionato,
        progetto_selezionato=progetto_selezionato,
        filtro_attestato=filtro_attestato,
        request_form=request.form  # Passa i filtri al template
    )

# Route per generare un PDF
@report_bp.route('/stampa_pdf')
def stampa_pdf():
    # Recupera i dati da visualizzare nel PDF
    progetti = Progetto.query.all()
    corsi = Corso.query.all()
    discenti = Discente.query.all()
    iscrizioni = Iscrizione.query.all()

    # Renderizza il template HTML per il PDF
    html_content = render_template(
        'report_pdf.html',
        progetti=progetti,
        corsi=corsi,
        discenti=discenti,
        iscrizioni=iscrizioni
    )

    # Genera il PDF
    from weasyprint import HTML
    pdf = HTML(string=html_content).write_pdf()

    # Restituisci il PDF come download
    return send_file(
        BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='report.pdf'
    )

@report_bp.route('/genera_excel', methods=['GET', 'POST'])
def genera_excel():
    if request.method == 'GET':
        # Recupera tutti i corsi per popolare il menu a tendina
        corsi = Corso.query.all()
        return render_template('report_excel.html', corsi=corsi)
    
    # Recupera i filtri dal form
    corso_id = request.form.get('corso_id')
    data_inizio = request.form.get('data_inizio')
    data_fine = request.form.get('data_fine')

    # Query per recuperare i dati filtrati
    query = Iscrizione.query.join(Corso).join(Discente)
    if corso_id:
        query = query.filter(Iscrizione.corso_id == corso_id)
    if data_inizio and data_fine:
        query = query.filter(Discente.data_iscrizione.between(data_inizio, data_fine))
    
    iscrizioni = query.all()

    # Converti i dati in un DataFrame pandas
    data = []
    for iscrizione in iscrizioni:
        data.append({
            'Nome': iscrizione.discente.nome,
            'Cognome': iscrizione.discente.cognome,
            'Email': iscrizione.discente.email,
            'Corso': iscrizione.corso.nome,
            'Ore Frequentate': iscrizione.ore_frequentate,
            'Punteggio Test Finale': iscrizione.punteggio_test,
            'Test Superato': 'Sì' if iscrizione.test_superato else 'No',
            'Attestato Rilasciato': 'Sì' if iscrizione.puo_ricevere_attestato() else 'No'
        })

    df = pd.DataFrame(data)

    # Genera un file Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    output.seek(0)

    # Restituisci il file come download
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='report.xlsx')