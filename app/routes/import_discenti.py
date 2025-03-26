import os
import pandas as pd
from flask import Blueprint, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app.models.models import db, Discente

import_discenti_bp = Blueprint('import_discenti', __name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@import_discenti_bp.route('/importa_discenti', methods=['POST'])
def importa_discenti():
    if 'file' not in request.files:
        flash('Nessun file selezionato', 'danger')
        return redirect(request.referrer)

    file = request.files['file']

    if file.filename == '':
        flash('Seleziona un file valido', 'danger')
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath)

            for _, row in df.iterrows():
                codice_fiscale = row['Codice Fiscale']
                esistente = Discente.query.filter_by(codice_fiscale=codice_fiscale).first()

                if not esistente:
                    nuovo_discente = Discente(
                        nome=row['Nome'],
                        cognome=row['Cognome'],
                        codice_fiscale=row['Codice Fiscale'],
                        email=row.get('Email', ''),
                        telefono=row.get('Telefono', ''),
                        ruolo=row.get('Ruolo', ''),
                        password_hash='',
                        progetto_id=request.form.get('progetto_id', 1)  # Usa il progetto selezionato dal form o un valore predefinito
                    )
                    db.session.add(nuovo_discente)

            db.session.commit()
            flash('Discenti importati con successo!', 'success')

        except Exception as e:
            flash(f'Errore nell’importazione: {str(e)}', 'danger')

        return redirect(url_for('discenti.lista_discenti'))  # ✅ Indentazione corretta

    flash('Formato file non supportato', 'danger')
    return redirect(request.referrer)
