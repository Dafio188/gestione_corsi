from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timezone
from flask_migrate import Migrate
from io import BytesIO
from flask_wtf.csrf import CSRFProtect
from flask import make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
import pandas as pd
import random
import string
import xlsxwriter
from extensions import db  # Import db from extensions
from routes import progetti
from models import Progetto, User, Corso, Iscrizione, Test, Nota, RisultatoTest, Attestato, Progetto, Nota  # Import all models
import secrets
import csv
import io
from routes.calendario import calendario_bp
from models import DisponibilitaDocente
from routes.disponibilita import disponibilita_bp

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip'}

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'test'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'attestati'), exist_ok=True)

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Initialize database with the app
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize login manager
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina'
login_manager.login_message_category = 'warning'

# Registra i blueprints
app.register_blueprint(disponibilita_bp)
app.register_blueprint(calendario_bp)

# Configurazione del login manager e altre impostazioni
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Decoratore per controllo ruoli
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"Role check for user: {current_user.username}, user ruolo: {current_user.ruolo}, required roles: {roles}")
            if not current_user.is_authenticated or current_user.ruolo not in roles:
                flash('Non hai i permessi per accedere a questa pagina', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Add this after creating the app but before defining routes
@app.context_processor
def utility_processor():
    return {
        'User': User,
        'datetime': datetime
    }

# Rotte per autenticazione
@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect based on user ruolo
        if current_user.ruolo == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.ruolo == 'docente':
            return redirect(url_for('docente_dashboard'))
        else:  # discente
            return redirect(url_for('discente_dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on user ruolo
        if current_user.ruolo == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.ruolo == 'docente':
            return redirect(url_for('docente_dashboard'))
        else:  # discente
            return redirect(url_for('discente_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login effettuato con successo', 'success')
            
            # Redirect based on user ruolo
            if user.ruolo == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.ruolo == 'docente':
                return redirect(url_for('docente_dashboard'))
            else:  # discente
                return redirect(url_for('discente_dashboard'))
        else:
            flash('Username o password non validi', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.ruolo == 'admin':
        # Get data for admin dashboard
        progetti = Progetto.query.all()
        corsi = Corso.query.all()
        discenti = User.query.filter_by(role='discente').all()
        docenti = User.query.filter_by(role='docente').all()
        test_completati = RisultatoTest.query.count()
        attestati = Attestato.query.all()
        
        return render_template('admin/dashboard.html', 
                              progetti=progetti,
                              corsi=corsi,
                              discenti=discenti,
                              docenti=docenti,
                              test_completati=test_completati,
                              attestati=attestati)
    elif current_user.ruolo == 'docente':
        return redirect(url_for('docente_corsi'))
    elif current_user.ruolo == 'discente':
        return redirect(url_for('discente_corsi'))
    else:
        flash('Ruolo non riconosciuto', 'danger')
        return redirect(url_for('logout'))

# Rotte per admin
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    discenti_count = User.query.filter_by(role='discente').count()
    docenti_count = User.query.filter_by(role='docente').count()
    corsi_count = Corso.query.count()
    test_count = Test.query.count()
    progetti_count = Progetto.query.count()
    attestati_count = Attestato.query.count()
    
    return render_template('admin/dashboard.html', 
                          discenti_count=discenti_count,
                          docenti_count=docenti_count,
                          corsi_count=corsi_count,
                          test_count=test_count,
                          progetti_count=progetti_count,
                          attestati_count=attestati_count)

# Add this route after your admin_dashboard route
@app.route('/admin/progetti')
@login_required
@role_required(['admin'])
def admin_progetti():
    progetti = Progetto.query.all()
    return render_template('admin/progetti.html', progetti=progetti)

@app.route('/admin/utenti')
@login_required
@role_required(['admin'])
def admin_utenti():
    utenti = User.query.all()
    return render_template('admin/utenti.html', utenti=utenti)

@app.route('/admin/utenti/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuovo_utente():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Verifica se l'utente esiste già
        if User.query.filter_by(username=username).first():
            flash('Username già in uso', 'danger')
            return redirect(url_for('admin_nuovo_utente'))
            
        if User.query.filter_by(email=email).first():
            flash('Email già in uso', 'danger')
            return redirect(url_for('admin_nuovo_utente'))
        
        # Crea nuovo utente
        utente = User(
            username=username,
            email=email,
            nome=nome,
            cognome=cognome,
            role=role
        )
        utente.set_password(password)
        
        db.session.add(utente)
        db.session.commit()
        
        flash('Utente creato con successo', 'success')
        return redirect(url_for('admin_utenti'))
        
    return render_template('admin/nuovo_utente.html')

# Aggiungi questa rotta al tuo file run.py
@app.route('/admin/importa-discenti', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_importa_discenti():
    risultati = None
    progetti = Progetto.query.all()
    
    if request.method == 'POST':
        # Verifica se è stato caricato un file
        if 'file' not in request.files:
            flash('Nessun file selezionato', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Verifica se il file ha un nome
        if file.filename == '':
            flash('Nessun file selezionato', 'danger')
            return redirect(request.url)
            
        # Verifica se il file è un Excel
        if not file.filename.endswith('.xlsx'):
            flash('Il file deve essere in formato Excel (.xlsx)', 'danger')
            return redirect(request.url)
        
        # Password predefinita
        password_default = request.form.get('password_default', 'Password123')
        
        try:
            # Leggi il file Excel
            df = pd.read_excel(file)
            
            # Inizializza contatori
            importati = 0
            saltati = 0
            errori = []
            progetti_non_trovati = set()
            
            # Itera sulle righe del dataframe
            for index, row in df.iterrows():
                try:
                    # Estrai i dati
                    codice_fiscale = str(row['Codice Fiscale']).strip() if not pd.isna(row['Codice Fiscale']) else ""
                    nome_cognome = str(row['Inserisci il tuo Nome e Cognome']).strip() if not pd.isna(row['Inserisci il tuo Nome e Cognome']) else ""
                    eta_str = str(row['Indicare la tua età']).strip() if not pd.isna(row['Indicare la tua età']) else ""
                    ruolo_ente = str(row['Ruolo all\'interno dell\'ente']).strip() if not pd.isna(row['Ruolo all\'interno dell\'ente']) else ""
                    email = str(row['Email']).strip() if not pd.isna(row['Email']) else ""
                    unita_org = str(row['Unità Organizzativa/Dipartimento di Appartenenza (Opzionale)']).strip() if not pd.isna(row['Unità Organizzativa/Dipartimento di Appartenenza (Opzionale)']) else ""
                    dipartimento_altro = str(row['Specifica il tuo Dipartimento (Solo se hai scelto \'Altro\' sopra)']).strip() if not pd.isna(row['Specifica il tuo Dipartimento (Solo se hai scelto \'Altro\' sopra)']) else ""
                    
                    # Estrai il nome del progetto dalla colonna "Ente di appartenenza"
                    nome_progetto = str(row['Ente di appartenenza']).strip() if not pd.isna(row['Ente di appartenenza']) else ""
                    
                    # Dividi nome e cognome
                    parti_nome = nome_cognome.split(' ', 1)
                    nome = parti_nome[0] if len(parti_nome) > 0 else ""
                    cognome = parti_nome[1] if len(parti_nome) > 1 else ""
                    
                    # Verifica se l'email è valida
                    if not email or '@' not in email:
                        errori.append(f"Riga {index+2}: Email non valida o mancante ({email})")
                        continue
                    
                    # Verifica se l'utente esiste già
                    if User.query.filter_by(email=email).first():
                        saltati += 1
                        continue
                    
                    # Trova il progetto corrispondente
                    progetto = None
                    if nome_progetto:
                        progetto = Progetto.query.filter(Progetto.titolo.ilike(f"%{nome_progetto}%")).first()
                        if not progetto:
                            progetti_non_trovati.add(nome_progetto)
                            errori.append(f"Riga {index+2}: Progetto non trovato ({nome_progetto})")
                            continue
                    else:
                        errori.append(f"Riga {index+2}: Nome progetto mancante")
                        continue
                    
                    # Genera username unico basato su nome e cognome
                    base_username = f"{nome.lower()}.{cognome.lower()}".replace(' ', '')
                    username = base_username
                    counter = 1
                    
                    # Assicurati che lo username sia unico
                    while User.query.filter_by(username=username).first():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    # Crea nuovo utente
                    utente = User(
                        username=username,
                        email=email,
                        nome=nome,
                        cognome=cognome,
                        role='discente',
                        # Aggiungi i campi aggiuntivi
                        codice_fiscale=codice_fiscale,
                        eta=eta_str,
                        ruolo_ente=ruolo_ente,
                        unita_org=unita_org,
                        dipartimento=dipartimento_altro if unita_org == 'Altro' else unita_org,
                        progetto_id=progetto.id  # Associa al progetto trovato
                    )
                    utente.set_password(password_default)
                    
                    db.session.add(utente)
                    importati += 1
                    
                except Exception as e:
                    errori.append(f"Riga {index+2}: {str(e)}")
            
            # Commit delle modifiche
            db.session.commit()
            
            # Aggiungi informazioni sui progetti non trovati
            if progetti_non_trovati:
                flash(f'Attenzione: i seguenti progetti non sono stati trovati: {", ".join(progetti_non_trovati)}', 'warning')
            
            risultati = {
                'importati': importati,
                'saltati': saltati,
                'errori': errori,
                'progetti_non_trovati': list(progetti_non_trovati)
            }
            
            flash(f'Importazione completata: {importati} discenti importati, {saltati} saltati', 'success')
            
        except Exception as e:
            flash(f'Errore durante l\'importazione: {str(e)}', 'danger')
    
    return render_template('admin/importa_discenti.html', risultati=risultati, progetti=progetti)

@app.route('/admin/iscrizioni/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuova_iscrizione():
    if request.method == 'POST':
        discente_id = request.form.get('discente_id')
        corso_id = request.form.get('corso_id')
        
        # Verifica se l'iscrizione esiste già
        iscrizione_esistente = Iscrizione.query.filter_by(
            discente_id=discente_id, 
            corso_id=corso_id
        ).first()
        
        if iscrizione_esistente:
            flash('Iscrizione già esistente', 'warning')
            return redirect(url_for('admin_nuova_iscrizione'))
        
        # Crea nuova iscrizione
        iscrizione = Iscrizione(
            discente_id=discente_id,
            corso_id=corso_id,
            ore_frequentate=0
        )
        
        db.session.add(iscrizione)
        db.session.commit()
        
        flash('Iscrizione creata con successo', 'success')
        return redirect(url_for('admin_corsi'))
    
    # Ottieni tutti i discenti e corsi per il form
    discenti = User.query.filter_by(ruolo='discente').all()
    corsi = Corso.query.all()
    
    # Se viene passato un corso_id come parametro, pre-selezionalo
    corso_id = request.args.get('corso_id')
    
    return render_template('admin/nuova_iscrizione.html', 
                          discenti=discenti, 
                          corsi=corsi,
                          corso_id=corso_id)

@app.route('/admin/utenti/modifica/<int:utente_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_modifica_utente(utente_id):
    utente = User.query.filter_by(id=utente_id).first_or_404()
    progetti = Progetto.query.all()
    
    if request.method == 'POST':
        # Extract form data
        username = request.form.get('username')
        email = request.form.get('email')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        role = request.form.get('role')
        password = request.form.get('password')
        codice_fiscale = request.form.get('codice_fiscale')
        unita_org = request.form.get('unita_org')
        progetto_id = request.form.get('progetto_id')
        
        # Check if username is already taken by another user
        existing_user = User.query.filter(User.username == username, User.id != utente_id).first()
        if existing_user:
            flash('Username già in uso', 'danger')
            return redirect(url_for('admin_modifica_utente', utente_id=utente_id))
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != utente_id).first()
        if existing_user:
            flash('Email già in uso', 'danger')
            return redirect(url_for('admin_modifica_utente', utente_id=utente_id))
        
        # Update user information
        utente.username = username
        utente.email = email
        utente.nome = nome
        utente.cognome = cognome
        utente.role = role
        utente.codice_fiscale = codice_fiscale
        utente.unita_org = unita_org
        
        # Only update progetto_id if the role is 'discente'
        if role == 'discente':
            utente.progetto_id = progetto_id if progetto_id else None
        else:
            utente.progetto_id = None
        
        # Update password if provided
        if password:
            utente.set_password(password)
        
        db.session.commit()
        flash('Utente aggiornato con successo', 'success')
        return redirect(url_for('admin_utenti'))
    
    return render_template('admin/modifica_utente.html', utente=utente, progetti=progetti)

@app.route('/admin/utenti/elimina/<int:utente_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_elimina_utente(utente_id):
    utente = User.query.filter_by(id=utente_id).first_or_404()
    
    # Non permettere l'eliminazione dell'utente corrente
    if utente.id == current_user.id:
        flash('Non puoi eliminare il tuo account', 'danger')
        return redirect(url_for('admin_utenti'))
    
    try:
        # Trova tutte le iscrizioni dell'utente
        iscrizioni = Iscrizione.query.filter_by(discente_id=utente_id).all()
        
        # Per ogni iscrizione, elimina i risultati dei test e gli attestati
        for iscrizione in iscrizioni:
            # Elimina i risultati dei test
            RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).delete()
            
            # Elimina gli attestati
            Attestato.query.filter_by(iscrizione_id=iscrizione.id).delete()
            
            # Elimina l'iscrizione
            db.session.delete(iscrizione)
        
        # Se l'utente è un docente, gestisci i corsi associati
        if utente.role == 'docente':
            # Opzione 1: Imposta il docente_id a NULL per i corsi
            # Corso.query.filter_by(docente_id=utente_id).update({Corso.docente_id: None})
            
            # Opzione 2: Elimina i corsi (e tutte le iscrizioni associate)
            corsi = Corso.query.filter_by(docente_id=utente_id).all()
            for corso in corsi:
                # Elimina tutti i test associati al corso
                test_list = Test.query.filter_by(corso_id=corso.id).all()
                for test in test_list:
                    # Elimina tutti i risultati dei test
                    RisultatoTest.query.filter_by(test_id=test.id).delete()
                    db.session.delete(test)
                
                # Trova tutte le iscrizioni al corso
                corso_iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
                for iscrizione in corso_iscrizioni:
                    # Elimina attestati
                    Attestato.query.filter_by(iscrizione_id=iscrizione.id).delete()
                    # Elimina l'iscrizione
                    db.session.delete(iscrizione)
                
                # Elimina il corso
                db.session.delete(corso)
        
        # Elimina l'utente
        db.session.delete(utente)
        db.session.commit()
        
        flash('Utente eliminato con successo', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
    
    return redirect(url_for('admin_utenti'))  

# After the docente_salva_risultati_test route

@app.route('/admin/corsi/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuovo_corso():
    # Get all docenti and progetti for the form
    docenti = User.query.filter_by(ruolo='docente').all()
    progetti = Progetto.query.all()
    
    if request.method == 'POST':
        # Get form data
        titolo = request.form.get('titolo')
        docente_id = request.form.get('docente_id')
        data_inizio = request.form.get('data_inizio')
        data_fine = request.form.get('data_fine')
        ore_totali = request.form.get('ore_totali')
        progetto_id = request.form.get('progetto_id')
        descrizione = request.form.get('descrizione')
        modalita = request.form.get('modalita')
        link_webinar = request.form.get('link_webinar')
        
        # Validate webinar link if modalita is webinar or misto
        if modalita in ['webinar', 'misto']:
            if not link_webinar:
                flash('Per la modalità webinar è necessario specificare il link', 'danger')
                return render_template('admin/nuovo_corso.html', docenti=docenti, progetti=progetti)
            
            # Ensure the link starts with http:// or https://
            if not (link_webinar.startswith('http://') or link_webinar.startswith('https://')):
                link_webinar = 'https://' + link_webinar
        else:
            link_webinar = None
        
        # Handle file upload if present
        materiale_path = None
        if 'materiale' in request.files and request.files['materiale'].filename:
            file = request.files['materiale']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create a unique filename to avoid collisions
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'materiale', unique_filename)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                file.save(file_path)
                materiale_path = f"materiale/{unique_filename}"
        
        # Create new corso
        try:
            nuovo_corso = Corso(
                titolo=titolo,
                docente_id=docente_id,
                data_inizio=datetime.strptime(data_inizio, '%Y-%m-%d').date(),
                data_fine=datetime.strptime(data_fine, '%Y-%m-%d').date(),
                ore_totali=ore_totali,
                progetto_id=progetto_id,
                descrizione=descrizione,
                modalita=modalita,
                link_webinar=link_webinar,
                materiale=materiale_path
            )
            
            db.session.add(nuovo_corso)
            db.session.commit()
            
            flash('Corso creato con successo', 'success')
            return redirect(url_for('admin_corsi'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione del corso: {str(e)}', 'danger')
    
    return render_template('admin/nuovo_corso.html', docenti=docenti, progetti=progetti)

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/corsi/<int:corso_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_modifica_corso(corso_id):
    corso = db.session.get(Corso, corso_id)
    if not corso:
        abort(404)
    
    docenti = User.query.filter_by(role='docente').all()
    progetti = Progetto.query.all()
    
    if request.method == 'POST':
        # Update course information
        corso.titolo = request.form.get('titolo')
        corso.descrizione = request.form.get('descrizione')
        corso.ore_totali = float(request.form.get('ore_totali'))
        corso.data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        corso.data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        corso.progetto_id = request.form.get('progetto_id')
        corso.progetto_riferimento = request.form.get('progetto_riferimento')
        corso.docente_id = int(request.form.get('docente_id'))
        corso.modalita = request.form.get('modalita', 'in_house')
        
        # Campi specifici per modalità
        corso.indirizzo = request.form.get('indirizzo')
        corso.orario = request.form.get('orario')
        corso.link_webinar = request.form.get('link_webinar')
        corso.piattaforma = request.form.get('piattaforma')  # Add this line
        
        # Validate modalita-specific fields
        if corso.modalita == 'in_house' and not corso.indirizzo:
            flash('Per la modalità in-house è necessario specificare l\'indirizzo', 'danger')
            return render_template('admin/modifica_corso.html', corso=corso, docenti=docenti, progetti=progetti)
        
        if corso.modalita == 'webinar' and not corso.link_webinar:
            flash('Per la modalità webinar è necessario specificare il link', 'danger')
            return render_template('admin/modifica_corso.html', corso=corso, docenti=docenti, progetti=progetti)
            
        if corso.modalita == 'e_learning' and not corso.piattaforma:  # Add this validation
            flash('Per la modalità e-learning è necessario specificare la piattaforma', 'danger')
            return render_template('admin/modifica_corso.html', corso=corso, docenti=docenti, progetti=progetti)
        
        db.session.commit()
        flash('Corso aggiornato con successo', 'success')
        return redirect(url_for('admin_corsi'))
    
    return render_template('admin/modifica_corso.html', corso=corso, docenti=docenti, progetti=progetti)

@app.route('/admin/calendario/eventi')
@login_required
@role_required(['admin'])
def admin_calendario_eventi():
    # Recupera i parametri di filtro
    docente_id = request.args.get('docente_id', type=int)
    corso_id = request.args.get('corso_id', type=int)
    stato = request.args.get('stato')
    
    # Log dei parametri
    print(f"Parametri ricevuti: docente_id={docente_id}, corso_id={corso_id}, stato={stato}")
    # Query base
    query = DisponibilitaDocente.query
    
    # Applica i filtri
    if docente_id:
        query = query.filter_by(docente_id=docente_id)
    if corso_id:
        query = query.filter_by(corso_id=corso_id)
    if stato:
        query = query.filter_by(stato=stato)
    
    # Recupera gli eventi
    eventi = query.all()
    # Log degli eventi
    print(f"Eventi trovati: {len(eventi)}")
    # Converti gli eventi in formato JSON
    return jsonify([evento.to_dict() for evento in eventi])


# Rotte per docenti
@app.route('/docente/dashboard')
@login_required
@role_required(['docente'])
def docente_dashboard():
    # Qui puoi aggiungere la logica per recuperare i dati necessari per la dashboard del docente
    # Ad esempio, i corsi che il docente sta insegnando
    corsi_docente = Corso.query.filter_by(docente_id=current_user.id).all()
    
    return render_template('docente/dashboard.html', 
                          corsi_count=len(corsi_docente),
                          corsi=corsi_docente)

@app.route('/docente/corsi')
@login_required
@role_required(['docente'])
def docente_corsi():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/corsi.html', corsi=corsi)

@app.route('/docente/corsi/<int:corso_id>')
@login_required
@role_required(['docente'])
def docente_dettaglio_corso(corso_id):
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
    test = Test.query.filter_by(corso_id=corso.id).all()
    return render_template('docente/dettaglio_corso.html', corso=corso, iscrizioni=iscrizioni, test=test)

@app.route('/docente/corsi/<int:corso_id>/iscrizioni/<int:iscrizione_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_modifica_iscrizione(corso_id, iscrizione_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Get the enrollment
    iscrizione = Iscrizione.query.filter_by(id=iscrizione_id).first_or_404()
    
    # Verify that the enrollment belongs to the course
    if iscrizione.corso_id != corso_id:
        abort(404)
    
    if request.method == 'POST':
        # Update enrollment hours
        ore_frequentate = request.form.get('ore_frequentate', 0)
        iscrizione.ore_frequentate = float(ore_frequentate) if ore_frequentate else 0
        
        db.session.commit()
        flash('Ore frequentate aggiornate con successo', 'success')
        return redirect(url_for('docente_dettaglio_corso', corso_id=corso_id))
    
    return render_template('docente/modifica_iscrizione.html', corso=corso, iscrizione=iscrizione)

@app.route('/docente/corsi/<int:corso_id>/test/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_nuovo_test(corso_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        titolo = request.form.get('titolo')
        forms_link = request.form.get('forms_link')
        
        # Gestione upload file
        file = request.files.get('file')
        file_path = None
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
        
        # Crea nuovo test
        test = Test(
            corso_id=corso_id,
            tipo=tipo,
            titolo=titolo,
            file_path=file_path,
            forms_link=forms_link
        )
        
        db.session.add(test)
        db.session.commit()
        
        flash('Test creato con successo', 'success')
        return redirect(url_for('docente_dettaglio_corso', corso_id=corso_id))
        
    return render_template('docente/nuovo_test.html', corso=corso)

@app.route('/docente/corsi/<int:corso_id>/test/<int:test_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_modifica_test(corso_id, test_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Get the test
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Verify that the test belongs to the course
    if test.corso_id != corso_id:
        abort(404)
    
    if request.method == 'POST':
        # Update test information
        test.tipo = request.form.get('tipo')
        test.titolo = request.form.get('titolo')
        test.forms_link = request.form.get('forms_link')
        
        # Handle file upload if a new file is provided
        file = request.files.get('file')
        if file and file.filename != '':
            # Save the new file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            # Update the file path
            test.file_path = file_path
        
        db.session.commit()
        flash('Test aggiornato con successo', 'success')
        return redirect(url_for('docente_dettaglio_corso', corso_id=corso_id))
    
    return render_template('docente/modifica_test.html', corso=corso, test=test)

@app.route('/docente/corsi/<int:corso_id>/test/<int:test_id>/elimina', methods=['POST'])
@login_required
@role_required(['docente'])
def docente_elimina_test(corso_id, test_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Get the test
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Verify that the test belongs to the course
    if test.corso_id != corso_id:
        abort(404)
    
    # Delete all test results associated with this test
    risultati = RisultatoTest.query.filter_by(test_id=test_id).all()
    for risultato in risultati:
        db.session.delete(risultato)
    
    # Delete the test
    db.session.delete(test)
    db.session.commit()
    
    flash('Test eliminato con successo', 'success')
    return redirect(url_for('docente_dettaglio_corso', corso_id=corso_id))

@app.route('/docente/corsi/<int:corso_id>/test/<int:test_id>')
@login_required
@role_required(['docente'])
def docente_dettaglio_test(corso_id, test_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Get the test
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Verify that the test belongs to the course
    if test.corso_id != corso_id:
        abort(404)
    
    # Get all enrollments for this course
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    
    # Get test results for each enrollment
    risultati = {}
    for iscrizione in iscrizioni:
        risultato = RisultatoTest.query.filter_by(
            test_id=test_id,
            iscrizione_id=iscrizione.id
        ).first()
        
        if risultato:
            risultati[iscrizione.id] = risultato
    
    return render_template('docente/dettaglio_test.html', 
                          corso=corso, 
                          test=test, 
                          iscrizioni=iscrizioni,
                          risultati=risultati)

@app.route('/docente/corsi/<int:corso_id>/test/<int:test_id>/risultati', methods=['POST'])
@login_required
@role_required(['docente'])
def docente_salva_risultati_test(corso_id, test_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Get the test
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Verify that the test belongs to the course
    if test.corso_id != corso_id:
        abort(404)
    
    # Get all enrollments for this course
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    
    # Process form data
    for iscrizione in iscrizioni:
        punteggio_key = f'punteggio_{iscrizione.id}'
        superato_key = f'superato_{iscrizione.id}'
        
        if punteggio_key in request.form and request.form.get(punteggio_key):
            punteggio = float(request.form.get(punteggio_key, 0))
            superato = superato_key in request.form
            
            # Check if result already exists
            risultato = RisultatoTest.query.filter_by(
                test_id=test_id,
                iscrizione_id=iscrizione.id
            ).first()
            
            if risultato:
                # Update existing result
                risultato.punteggio = punteggio
                risultato.superato = superato
                risultato.data_completamento = datetime.utcnow()
            else:
                # Create new result
                risultato = RisultatoTest(
                    test_id=test_id,
                    iscrizione_id=iscrizione.id,
                    punteggio=punteggio,
                    superato=superato
                )
                db.session.add(risultato)
    
    db.session.commit()
    flash('Risultati del test salvati con successo', 'success')
    return redirect(url_for('docente_dettaglio_test', corso_id=corso_id, test_id=test_id))

@app.route('/docente/corsi/<int:corso_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_modifica_corso(corso_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    progetti = Progetto.query.all()
    
    if request.method == 'POST':
        # Update course information
        corso.titolo = request.form.get('titolo')
        corso.descrizione = request.form.get('descrizione')
        corso.ore_totali = float(request.form.get('ore_totali'))
        corso.data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        corso.data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        corso.progetto_id = request.form.get('progetto_id')
        corso.progetto_riferimento = request.form.get('progetto_riferimento')
        
        # Get modalita and related fields
        corso.modalita = request.form.get('modalita', 'in_house')
        corso.indirizzo = request.form.get('indirizzo')
        corso.link_webinar = request.form.get('link_webinar')
        corso.piattaforma = request.form.get('piattaforma')  # Add this line
        corso.orario = request.form.get('orario')
        
        # Validate modalita-specific fields
        if corso.modalita == 'in_house' and not corso.indirizzo:
            flash('Per la modalità in-house è necessario specificare l\'indirizzo', 'danger')
            return render_template('docente/modifica_corso.html', corso=corso, progetti=progetti)
        
        if corso.modalita == 'webinar' and not corso.link_webinar:
            flash('Per la modalità webinar è necessario specificare il link', 'danger')
            return render_template('docente/modifica_corso.html', corso=corso, progetti=progetti)
        
        if corso.modalita == 'e_learning' and not corso.piattaforma:  # Add this validation
            flash('Per la modalità e-learning è necessario specificare la piattaforma', 'danger')
            return render_template('docente/modifica_corso.html', corso=corso, progetti=progetti)
        
        db.session.commit()
        flash('Corso aggiornato con successo', 'success')
        return redirect(url_for('docente_corsi'))
    
    return render_template('docente/modifica_corso.html', corso=corso, progetti=progetti)

@app.route('/docente/corsi/<int:corso_id>/elimina', methods=['POST'])
@login_required
@role_required(['docente'])
def docente_elimina_corso(corso_id):
    # Verify that the course belongs to the current docente
    corso = Corso.query.filter_by(id=corso_id, docente_id=current_user.id).first_or_404()
    
    # Check if there are any enrollments for this course
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    
    # If there are enrollments, don't allow deletion
    if iscrizioni:
        flash('Non è possibile eliminare un corso con iscrizioni attive', 'danger')
        return redirect(url_for('docente_corsi'))
    
    # Delete tests associated with this course
    tests = Test.query.filter_by(corso_id=corso_id).all()
    for test in tests:
        db.session.delete(test)
    
    # Delete the course
    db.session.delete(corso)
    db.session.commit()
    
    flash('Corso eliminato con successo', 'success')
    return redirect(url_for('docente_corsi'))

# Then add these routes to your run.py file
@app.route('/docente/note', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_note():
    # Recupera tutte le note del docente
    note = Nota.query.filter_by(docente_id=current_user.id).all()
    
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        contenuto = request.form.get('contenuto')
        corso_id = request.form.get('corso_id') or None
        
        # Crea una nuova nota
        nuova_nota = Nota(
            titolo=titolo,
            contenuto=contenuto,
            docente_id=current_user.id,
            corso_id=corso_id
        )
        
        db.session.add(nuova_nota)
        db.session.commit()
        
        flash('Nota salvata con successo', 'success')
        return redirect(url_for('docente_note'))
    
    # Recupera i corsi del docente per il dropdown
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    
    return render_template('docente/note.html', note=note, corsi=corsi)

@app.route('/docente/note/<int:nota_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_modifica_nota(nota_id):
    # Recupera la nota
    nota = Nota.query.filter_by(id=nota_id, docente_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        nota.titolo = request.form.get('titolo')
        nota.contenuto = request.form.get('contenuto')
        nota.corso_id = request.form.get('corso_id') or None
        
        db.session.commit()
        flash('Nota aggiornata con successo', 'success')
        return redirect(url_for('docente_note'))
    
    # Recupera i corsi del docente per il dropdown
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    
    return render_template('docente/modifica_nota.html', nota=nota, corsi=corsi)

@app.route('/docente/note/<int:nota_id>/elimina', methods=['POST'])
@login_required
@role_required(['docente'])
def docente_elimina_nota(nota_id):
    # Recupera la nota
    nota = Nota.query.filter_by(id=nota_id, docente_id=current_user.id).first_or_404()
    
    db.session.delete(nota)
    db.session.commit()
    
    flash('Nota eliminata con successo', 'success')
    return redirect(url_for('docente_note'))

# Rotte per gestione docenti
@app.route('/admin/docenti')
@login_required
@role_required(['admin'])
def admin_docenti():
    docenti = User.query.filter_by(ruolo='docente').all()
    return render_template('admin/docenti.html', docenti=docenti)

@app.route('/admin/docenti/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuovo_docente():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        password = request.form.get('password')
        
        # Verifica se l'utente esiste già
        if User.query.filter_by(username=username).first():
            flash('Username già in uso', 'danger')
            return redirect(url_for('admin_nuovo_docente'))
            
        if User.query.filter_by(email=email).first():
            flash('Email già in uso', 'danger')
            return redirect(url_for('admin_nuovo_docente'))
        
        # Crea nuovo docente
        docente = User(
            username=username,
            email=email,
            nome=nome,
            cognome=cognome,
            role='docente'
        )
        docente.set_password(password)
        
        db.session.add(docente)
        db.session.commit()
        
        flash('Docente creato con successo', 'success')
        return redirect(url_for('admin_docenti'))
        
    return render_template('admin/nuovo_docente.html')

@app.route('/admin/corsi')
@login_required
@role_required(['admin'])
def admin_corsi():
    corsi = Corso.query.all()
    docenti = User.query.filter_by(role='docente').all()
    progetti = Progetto.query.all()
    now = datetime.now().date()  # Convertiamo in date senza timezone
    
    return render_template('admin/corsi.html', 
                         corsi=corsi, 
                         docenti=docenti, 
                         progetti=progetti,
                         now=now)

@app.route('/admin/corsi/<int:corso_id>')
@login_required
@role_required(['admin'])
def admin_dettaglio_corso(corso_id):
    corso = db.session.get(Corso, corso_id)
    if not corso:
        abort(404)
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    test = Test.query.filter_by(corso_id=corso_id).all()
    
    # Make sure each iscrizione has its discente loaded
    for iscrizione in iscrizioni:
        iscrizione.discente = db.session.get(User, iscrizione.discente_id)  # Use db.session.get instead of Query.get
    
    return render_template('admin/dettaglio_corso.html', 
                          corso=corso, 
                          iscrizioni=iscrizioni,
                          test=test)

@app.route('/docente/corsi/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_nuovo_corso():
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        descrizione = request.form.get('descrizione')
        ore_totali = float(request.form.get('ore_totali'))
        data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        progetto_id = request.form.get('progetto_id')
        progetto_riferimento = request.form.get('progetto_riferimento')
        
        # For docente, we use the current user's ID
        docente_id = current_user.id
        modalita = request.form.get('modalita', 'in_house')
        indirizzo = request.form.get('indirizzo')
        link_webinar = request.form.get('link_webinar')
        piattaforma = request.form.get('piattaforma')  # Add this line
        orario = request.form.get('orario')
        
        # Validate modalita-specific fields
        if modalita == 'in_house' and not indirizzo:
            flash('Per la modalità in-house è necessario specificare l\'indirizzo', 'danger')
            progetti = Progetto.query.all()
            return render_template('docente/nuovo_corso.html', progetti=progetti)
        
        if modalita == 'webinar' and not link_webinar:
            flash('Per la modalità webinar è necessario specificare il link', 'danger')
            progetti = Progetto.query.all()
            return render_template('docente/nuovo_corso.html', progetti=progetti)
            
        if modalita == 'e_learning' and not piattaforma:  # Add this validation
            flash('Per la modalità e-learning è necessario specificare la piattaforma', 'danger')
            progetti = Progetto.query.all()
            return render_template('docente/nuovo_corso.html', progetti=progetti)

        corso = Corso(
            titolo=titolo,
            descrizione=descrizione,
            ore_totali=ore_totali,
            data_inizio=data_inizio,
            data_fine=data_fine,
            progetto_riferimento=progetto_riferimento,
            progetto_id=progetto_id,
            docente_id=docente_id,
            modalita=modalita,
            indirizzo=indirizzo,
            link_webinar=link_webinar,
            piattaforma=piattaforma,  # Add this line
            orario=orario
        )
        
        db.session.add(corso)
        db.session.commit()
        
        flash('Corso creato con successo', 'success')
        return redirect(url_for('docente_corsi'))
    
    progetti = Progetto.query.all()
    return render_template('docente/nuovo_corso.html', progetti=progetti)

@app.route('/admin/corsi/<int:corso_id>/elimina', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_elimina_corso(corso_id):
    corso = db.session.get(Corso, corso_id)
    if not corso:
        abort(404)
    
    # Check if there are any enrollments for this course
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    
    # Delete all enrollments and related data
    for iscrizione in iscrizioni:
        # Delete test results
        risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).all()
        for risultato in risultati:
            db.session.delete(risultato)
        
        # Delete certificates
        attestati = Attestato.query.filter_by(iscrizione_id=iscrizione.id).all()
        for attestato in attestati:
            db.session.delete(attestato)
        
        db.session.delete(iscrizione)
    
    # Delete tests associated with this course
    tests = Test.query.filter_by(corso_id=corso_id).all()
    for test in tests:
        db.session.delete(test)
    
    # Delete the course
    db.session.delete(corso)
    db.session.commit()
    
    flash('Corso eliminato con successo', 'success')
    return redirect(url_for('admin_corsi'))

@app.route('/admin/corsi/<int:corso_id>/iscrizioni/<int:iscrizione_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_modifica_iscrizione(corso_id, iscrizione_id):
    corso = db.session.get(Corso, corso_id)
    if not corso:
        abort(404)
    iscrizione = db.session.get(Iscrizione, iscrizione_id)
    if not iscrizione:
        abort(404)
    
    if request.method == 'POST':
        # Debug prints
        print("Form data:", request.form)
        print("CSRF token in form:", request.form.get('csrf_token'))
        # Remove the line that's causing the error
        # print("CSRF token in session:", csrf._get_token())
        
        try:
            # Update enrollment information
            ore_frequentate = request.form.get('ore_frequentate', 0)
            print("Ore frequentate (raw):", ore_frequentate)
            
            # Convert to float with error handling
            iscrizione.ore_frequentate = float(ore_frequentate) if ore_frequentate else 0
            
            db.session.commit()
            flash('Iscrizione aggiornata con successo', 'success')
            return redirect(url_for('admin_dettaglio_corso', corso_id=corso_id))
        except Exception as e:
            print("Error updating iscrizione:", str(e))
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'danger')
            return redirect(url_for('admin_modifica_iscrizione', corso_id=corso_id, iscrizione_id=iscrizione_id))
    
    return render_template('admin/modifica_iscrizione.html', corso=corso, iscrizione=iscrizione)

@app.route('/admin/corsi/<int:corso_id>/iscrizioni/<int:iscrizione_id>/elimina', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_elimina_iscrizione(corso_id, iscrizione_id):
    iscrizione = db.session.get(Iscrizione, iscrizione_id)
    if not iscrizione:
        abort(404)
    
    # Check if there are any test results associated with this enrollment
    risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione_id).all()
    for risultato in risultati:
        db.session.delete(risultato)
    
    # Check if there are any attestati associated with this enrollment
    attestati = Attestato.query.filter_by(iscrizione_id=iscrizione_id).all()
    for attestato in attestati:
        db.session.delete(attestato)
    
    db.session.delete(iscrizione)
    db.session.commit()
    
    flash('Iscrizione eliminata con successo', 'success')
    return redirect(url_for('admin_dettaglio_corso', corso_id=corso_id))


@app.route('/admin/test/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuovo_test():
    corsi = Corso.query.all()
    
    if request.method == 'POST':
        corso_id = request.form.get('corso_id')
        tipo = request.form.get('tipo')
        titolo = request.form.get('titolo')
        forms_link = request.form.get('forms_link')
        
        # Gestione upload file
        file = request.files.get('file')
        file_path = None
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
        
        # Crea nuovo test
        test = Test(
            corso_id=corso_id,
            tipo=tipo,
            titolo=titolo,
            file_path=file_path,
            forms_link=forms_link
        )
        
        db.session.add(test)
        db.session.commit()
        
        flash('Test creato con successo', 'success')
        return redirect(url_for('admin_test'))
        
    return render_template('admin/nuovo_test.html', corsi=corsi)

# Add this new route for editing tests
@app.route('/admin/test/<int:test_id>/modifica', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_modifica_test(test_id):
    test = Test.query.filter_by(id=test_id).first_or_404()
    corsi = Corso.query.all()
    
    if request.method == 'POST':
        # Update test information
        test.corso_id = request.form.get('corso_id')
        test.tipo = request.form.get('tipo')
        test.titolo = request.form.get('titolo')
        test.forms_link = request.form.get('forms_link')
        
        # Handle file upload if a new file is provided
        file = request.files.get('file')
        if file and file.filename != '':
            # Save the new file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            # Update the file path
            test.file_path = file_path
        
        db.session.commit()
        flash('Test aggiornato con successo', 'success')
        return redirect(url_for('admin_test'))
    
    return render_template('admin/modifica_test.html', test=test, corsi=corsi)

# Add this route for deleting tests
@app.route('/admin/test/<int:test_id>/elimina', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_elimina_test(test_id):
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Delete all test results associated with this test
    risultati = RisultatoTest.query.filter_by(test_id=test_id).all()
    for risultato in risultati:
        db.session.delete(risultato)
    
    # Delete the test
    db.session.delete(test)
    db.session.commit()
    
    flash('Test eliminato con successo', 'success')
    return redirect(url_for('admin_test'))   

@app.route('/admin/test/<int:test_id>/risultati', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_test_risultati(test_id):
    test = Test.query.filter_by(id=test_id).first_or_404()
    corso = db.session.get(Corso, test.corso_id)
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
    
    if request.method == 'POST':
        for iscrizione in iscrizioni:
            punteggio_key = f'punteggio_{iscrizione.id}'
            superato_key = f'superato_{iscrizione.id}'
            
            if punteggio_key in request.form:
                punteggio_value = request.form.get(punteggio_key, '')
                
                # Handle empty string or invalid input
                try:
                    punteggio = float(punteggio_value) if punteggio_value.strip() else 0
                except ValueError:
                    punteggio = 0
                    
                superato = superato_key in request.form
                
                # Check if result already exists
                risultato = RisultatoTest.query.filter_by(
                    test_id=test_id,
                    iscrizione_id=iscrizione.id
                ).first()
                
                if risultato:
                    # Update existing result
                    risultato.punteggio = punteggio
                    risultato.superato = superato
                else:
                    # Create new result
                    risultato = RisultatoTest(
                        test_id=test_id,
                        iscrizione_id=iscrizione.id,
                        punteggio=punteggio,
                        superato=superato
                    )
                    db.session.add(risultato)
        
        db.session.commit()
        flash('Risultati del test salvati con successo', 'success')
        return redirect(url_for('admin_test'))
    
    # Get existing results
    risultati = {}
    for iscrizione in iscrizioni:
        risultato = RisultatoTest.query.filter_by(
            test_id=test_id,
            iscrizione_id=iscrizione.id
        ).first()
        
        if risultato:
            risultati[iscrizione.id] = risultato
    
    return render_template('admin/test_risultati.html', 
                          test=test, 
                          corso=corso, 
                          iscrizioni=iscrizioni,
                          risultati=risultati)

# Add this helper function to process test results
def process_test_result(email, score_text, test_id, corso_id):
    """Process a single test result row"""
    # Try to convert score to float
    try:
        # Handle different formats (e.g., "80%", "8/10", or just "8")
        score_text = str(score_text).strip()
        if not score_text:
            return 0  # Skip empty scores
            
        if '%' in score_text:
            # Format: "80%"
            score = float(score_text.replace('%', ''))
        elif '/' in score_text:
            # Format: "8/10"
            num, den = score_text.split('/')
            score = (float(num.strip()) / float(den.strip())) * 100
        else:
            # Try to convert directly to float
            score_value = float(score_text)
            
            # If the score is less than 1, it might be a fraction (e.g., 0.8 for 80%)
            if score_value <= 1:
                score = score_value * 100
            else:
                score = score_value
    except ValueError as e:
        print(f"Error converting score '{score_text}' for email '{email}': {str(e)}")
        return 0  # Skip if score can't be converted
    
    # Find the user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"User not found with email: {email}")
        return 0  # Skip if user not found
    
    # Find the iscrizione for this user
    iscrizione = Iscrizione.query.filter_by(
        corso_id=corso_id,
        discente_id=user.id
    ).first()
    
    if not iscrizione:
        print(f"Iscrizione not found for user {user.id} in corso {corso_id}")
        return 0  # Skip if iscrizione not found
    
    # Check if result already exists
    risultato = RisultatoTest.query.filter_by(
        test_id=test_id,
        iscrizione_id=iscrizione.id
    ).first()
    
    # Determine if test is passed (85% or higher)
    superato = score >= 85
    
    if risultato:
        # Update existing result
        risultato.punteggio = score
        risultato.superato = superato
    else:
        # Create new result
        risultato = RisultatoTest(
            test_id=test_id,
            iscrizione_id=iscrizione.id,
            punteggio=score,
            superato=superato
        )
        db.session.add(risultato)
    
    return 1  # Count this as a successful import

# Rotte per gestione test
@app.route('/admin/test')
@login_required
@role_required(['admin'])
def admin_test():
    test = Test.query.all()
    return render_template('admin/test.html', test=test)

# Rotta per la pagina di caricamento dei risultati da Excel
@app.route('/admin/test/<int:test_id>/carica-risultati', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'docente'])
def admin_carica_risultati(test_id):
    test = Test.query.filter_by(id=test_id).first_or_404()
    corso = db.session.get(Corso, test.corso_id)
    
    if request.method == 'POST':
        file = request.files.get('file_excel')
        
        if file and file.filename:
            # Verifica che il file sia in formato Excel
            if not file.filename.endswith(('.xlsx', '.xls')):
                flash('Il file deve essere in formato Excel (.xlsx o .xls)', 'danger')
                return redirect(url_for('admin_test_risultati', test_id=test_id))
            
            # Salva temporaneamente il file
            filename = secure_filename(file.filename)
            temp_path = os.path.join('uploads', 'temp', filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            file.save(temp_path)
            
            try:
                # Leggi il file Excel con pandas
                import pandas as pd
                df = pd.read_excel(temp_path)
                
                # Processa i dati del file Excel
                # Colonne specifiche da utilizzare
                # F: Total points (punteggio) - indice 5
                # I: Nome - indice 8
                # L: Cognome - indice 11
                # O: Comune di appartenenza - indice 14
                # R: Indirizzo Email - indice 17
                
                if len(df.columns) < 18:  # Colonna R è indice 17
                    flash(f'Il file Excel non contiene tutte le colonne necessarie. Sono richieste almeno 18 colonne.', 'danger')
                    os.remove(temp_path)  # Rimuovi il file temporaneo
                    if current_user.role == 'admin':
                        return redirect(url_for('admin_test'))
                    else:
                        return redirect(url_for('docente_test'))
                
                # Ottieni tutti i discenti iscritti al corso
                iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
                discenti_emails = {iscrizione.discente.email.lower(): iscrizione.discente for iscrizione in iscrizioni}
                
                risultati_salvati = 0
                errori = 0
                
                for _, row in df.iterrows():
                    try:
                        # Estrai i dati dalle colonne specifiche
                        if len(row) > 17:  # Assicurati che ci siano abbastanza colonne
                            punteggio = row.iloc[5] if pd.notna(row.iloc[5]) else 0
                            email = str(row.iloc[17]).strip().lower() if pd.notna(row.iloc[17]) else ''
                            
                            # Verifica se l'email esiste nel sistema
                            if email in discenti_emails:
                                discente = discenti_emails[email]
                                
                                # Verifica se esiste già un risultato per questo test e iscrizione
                                iscrizione = Iscrizione.query.filter_by(
                                    corso_id=corso.id,
                                    discente_id=discente.id
                                ).first()
                                
                                if not iscrizione:
                                    print(f"Iscrizione non trovata per il discente {discente.email} nel corso {corso.id}")
                                    continue
                                    
                                risultato_esistente = RisultatoTest.query.filter_by(
                                    test_id=test_id,
                                    iscrizione_id=iscrizione.id
                                ).first()
                                
                                # Determina se il test è superato (punteggio >= 60%)
                                superato = float(punteggio) >= 60.0
                                
                                if risultato_esistente:
                                    # Aggiorna il risultato esistente
                                    risultato_esistente.punteggio = float(punteggio)
                                    risultato_esistente.superato = superato
                                    risultato_esistente.data_completamento = datetime.now()
                                else:
                                    # Crea un nuovo risultato
                                    nuovo_risultato = RisultatoTest(
                                        test_id=test_id,
                                        iscrizione_id=iscrizione.id,
                                        punteggio=float(punteggio),
                                        superato=superato,
                                        data_completamento=datetime.now()
                                    )
                                    db.session.add(nuovo_risultato)
                                
                                risultati_salvati += 1
                    except Exception as e:
                        print(f"Errore nell'elaborazione della riga: {str(e)}")
                        errori += 1
                
                # Commit delle modifiche al database
                db.session.commit()
                
                if risultati_salvati > 0:
                    flash(f'Risultati caricati con successo! {risultati_salvati} risultati importati.', 'success')
                else:
                    flash('Nessun risultato è stato importato. Verifica che le email nel file corrispondano a discenti iscritti al corso.', 'warning')
                
                if errori > 0:
                    flash(f'Ci sono stati {errori} errori durante l\'importazione. Controlla il formato del file.', 'warning')
                
            except Exception as e:
                flash(f'Errore durante l\'elaborazione del file: {str(e)}', 'danger')
            finally:
                # Rimuovi il file temporaneo
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            flash('Nessun file selezionato!', 'danger')
        
        return redirect(url_for('admin_test_risultati', test_id=test_id))
    
    return render_template('admin/carica_risultati_test.html', test=test, corso=corso)

# Rotta per l'importazione dei risultati da Microsoft Forms
@app.route('/admin/test/<int:test_id>/import-forms', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_import_forms_results(test_id):
    test = Test.query.filter_by(id=test_id).first_or_404()
    corso = db.session.get(Corso, test.corso_id)
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
    
    if request.method == 'POST':
        try:
            import_method = request.form.get('import_method', 'paste')
            
            if import_method == 'paste':
                # Get the forms data from the textarea
                forms_data = request.form.get('forms_data')
                
                # Parse the CSV data (assuming it's copied from Excel/Forms export)
                import csv
                from io import StringIO
                
                csv_data = StringIO(forms_data)
                reader = csv.reader(csv_data)
                
                # Skip header row
                headers = next(reader)
                
                # Find the columns for email and score
                email_col = None
                score_col = None
                
                for i, header in enumerate(headers):
                    header_lower = str(header).lower()
                    if 'email' in header_lower or 'posta elettronica' in header_lower:
                        email_col = i
                    if any(term in header_lower for term in ['punteggio', 'score', 'risultato', 'total points', 'total', 'points']):
                        score_col = i
                
                if email_col is None or score_col is None:
                    flash(f'Impossibile trovare le colonne per email e punteggio nei dati forniti. Colonne trovate: {", ".join(headers)}', 'danger')
                    return redirect(url_for('admin_import_forms_results', test_id=test_id))
                
                # Process each row
                results_count = 0
                for row in reader:
                    if len(row) <= max(email_col, score_col):
                        continue  # Skip incomplete rows
                    
                    email = row[email_col].strip()
                    score_text = row[score_col].strip()
                    
                    # Process the score and user data
                    results_count += process_test_result(email, score_text, test_id, corso.id)
                
                db.session.commit()
                flash(f'Importati {results_count} risultati da Microsoft Forms', 'success')
                
            elif import_method == 'excel':
                # Get the uploaded Excel file
                excel_file = request.files.get('excel_file')
                
                if not excel_file or not excel_file.filename:
                    flash('Nessun file Excel caricato', 'danger')
                    return redirect(url_for('admin_import_forms_results', test_id=test_id))
                
                # Check file extension
                if not excel_file.filename.endswith(('.xlsx', '.xls')):
                    flash('Il file deve essere in formato Excel (.xlsx o .xls)', 'danger')
                    return redirect(url_for('admin_import_forms_results', test_id=test_id))
                
                # Process the Excel file
                import pandas as pd
                
                # Read the Excel file
                df = pd.read_excel(excel_file)
                
                # Print all columns for debugging
                print("Available columns:", df.columns.tolist())
                
                # Find the columns for email and score
                email_col = None
                score_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'email' in col_lower or 'posta elettronica' in col_lower:
                        email_col = col
                        print(f"Found email column: {col}")
                    if any(term in col_lower for term in ['punteggio', 'score', 'risultato', 'total points', 'total', 'points']):
                        score_col = col
                        print(f"Found score column: {col}")
                
                if email_col is None or score_col is None:
                    flash(f'Impossibile trovare le colonne per email e punteggio nel file Excel. Colonne trovate: {", ".join(str(c) for c in df.columns)}', 'danger')
                    return redirect(url_for('admin_import_forms_results', test_id=test_id))
                
                # Process each row
                results_count = 0
                for _, row in df.iterrows():
                    email = str(row[email_col]).strip()
                    score_text = str(row[score_col]).strip()
                    
                    # Skip rows with empty email or score
                    if not email or email == 'nan' or not score_text or score_text == 'nan':
                        continue
                    
                    # Debug print
                    print(f"Processing: Email={email}, Score={score_text}")
                    
                    # Process the score and user data
                    results_count += process_test_result(email, score_text, test_id, corso.id)
                
                db.session.commit()
                flash(f'Importati {results_count} risultati dal file Excel', 'success')
                
            elif import_method == 'link':
                # Get the forms link
                forms_link = request.form.get('forms_link')
                
                if not forms_link:
                    flash('Inserisci un link valido di Microsoft Forms', 'danger')
                    return redirect(url_for('admin_import_forms_results', test_id=test_id))
                
                # Store the link in the test record for future use
                test.forms_link = forms_link
                db.session.commit()
                
                flash('Link salvato. Nota: l\'importazione diretta da link non è ancora supportata. Usa il metodo copia-incolla o carica un file Excel.', 'info')
            
            return redirect(url_for('admin_test_risultati', test_id=test_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'importazione: {str(e)}', 'danger')
    
    return render_template('admin/import_forms_results.html', test=test, corso=corso)
    
   # Rotte per gestione attestati
@app.route('/admin/attestati')
@login_required
@role_required(['admin'])
def admin_attestati():
    attestati = Attestato.query.all()
    
    # Get related data for each attestato
    for attestato in attestati:
        attestato.iscrizione = db.session.get(Iscrizione, attestato.iscrizione_id)
        if attestato.iscrizione:
            attestato.discente = db.session.get(User, attestato.iscrizione.discente_id)
            attestato.corso = db.session.get(Corso, attestato.iscrizione.corso_id)
    
    return render_template('admin/attestati.html', attestati=attestati)

# Add this route after your admin_attestati route
@app.route('/admin/report')
@login_required
@role_required(['admin'])
def admin_report():
    # Get data for reports
    progetti = Progetto.query.all()
    corsi = Corso.query.all()
    discenti = User.query.filter_by(role='discente').all()
    docenti = User.query.filter_by(role='docente').all()
    
    # You can add more complex statistics here
    
    return render_template('admin/report.html', 
                          progetti=progetti,
                          corsi=corsi,
                          discenti=discenti,
                          docenti=docenti)

@app.route('/admin/attestati/nuovo', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_nuovo_attestato():
    iscrizioni = Iscrizione.query.all()
    
    if request.method == 'POST':
        iscrizione_id = request.form.get('iscrizione_id')
        
        if not iscrizione_id:
            flash('Seleziona un\'iscrizione', 'danger')
            return redirect(url_for('admin_nuovo_attestato'))
            
        iscrizione = Iscrizione.query.get_or_404(int(iscrizione_id))
        discente = User.query.get_or_404(iscrizione.discente_id)
        corso = Corso.query.get_or_404(iscrizione.corso_id)
        
        # Check if attestato already exists
        existing_attestato = Attestato.query.filter_by(iscrizione_id=iscrizione_id).first()
        if existing_attestato:
            flash('Attestato già esistente per questa iscrizione', 'warning')
            return redirect(url_for('admin_nuovo_attestato'))
        
        # Check if the discente has completed all course hours
        if iscrizione.ore_frequentate < corso.ore_totali:
            flash(f'Il discente non ha completato tutte le ore del corso ({iscrizione.ore_frequentate}/{corso.ore_totali})', 'danger')
            return redirect(url_for('admin_nuovo_attestato'))
        
        # Check if the discente has passed the final test with at least 85%
        test_finale = Test.query.filter_by(corso_id=corso.id, tipo='finale').first()
        if test_finale:
            risultato = RisultatoTest.query.filter_by(
                test_id=test_finale.id,
                iscrizione_id=iscrizione.id
            ).first()
            
            if not risultato:
                flash('Il discente non ha sostenuto il test finale', 'danger')
                return redirect(url_for('admin_nuovo_attestato'))
            
            if not risultato.punteggio or risultato.punteggio < 85:
                flash(f'Il discente non ha ottenuto almeno l\'85% nel test finale (punteggio: {risultato.punteggio}%)', 'danger')
                return redirect(url_for('admin_nuovo_attestato'))
                
            valutazione = f"{risultato.punteggio}/100"
        else:
            valutazione = "N/A"
        
        # Generate PDF attestato
        try:
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"attestato_{discente.cognome}_{discente.nome}_{timestamp}.pdf"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'attestati', filename)
            
            # Generate the PDF
            generate_attestato_pdf(
                file_path,
                discente.nome,
                discente.cognome,
                discente.codice_fiscale or "N/A",
                discente.unita_org or "N/A",
                corso.titolo,
                f"{iscrizione.ore_frequentate}/{corso.ore_totali}",
                valutazione,
                corso.progetto.titolo if corso.progetto else "N/A",
                corso.modalita
            )
            
            # Create attestato record
            attestato = Attestato(
                iscrizione_id=iscrizione.id,
                corso_id=corso.id,  # Aggiungiamo il corso_id
                file_path=file_path,
                data_generazione=datetime.utcnow()
            )
            
            db.session.add(attestato)
            db.session.commit()
            
            flash('Attestato generato con successo', 'success')
            return redirect(url_for('admin_attestati'))
            
        except Exception as e:
            flash(f'Errore durante la generazione dell\'attestato: {str(e)}', 'danger')
            return redirect(url_for('admin_nuovo_attestato'))
        
    return render_template('admin/nuovo_attestato.html', iscrizioni=iscrizioni)

# Add this function before the admin_genera_attestati_automatici route
def generate_attestato_pdf(file_path, nome, cognome, codice_fiscale, unita_org, titolo_corso, ore_frequentate, valutazione, progetto, modalita):
    """
    Generate a PDF certificate (attestato) with the provided information.
    
    Args:
        file_path: Where to save the PDF file
        nome: First name of the student
        cognome: Last name of the student
        codice_fiscale: Tax code of the student
        unita_org: Organizational unit of the student
        titolo_corso: Course title
        ore_frequentate: Hours attended (format: "X/Y")
        valutazione: Evaluation score (format: "X/100")
        progetto: Project name
        modalita: Course modality
    """
    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the BytesIO buffer as its "file"
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=72, 
        leftMargin=72,
        topMargin=72, 
        bottomMargin=72
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 1  # Center alignment
    
    normal_style = styles['Normal']
    normal_style.alignment = 1  # Center alignment
    
    # Add title
    title = Paragraph(f"ATTESTATO DI PARTECIPAZIONE", title_style)
    elements.append(title)
    elements.append(Paragraph("<br/><br/>", normal_style))
    
    # Add certificate text
    elements.append(Paragraph(f"Si attesta che", normal_style))
    elements.append(Paragraph("<br/>", normal_style))
    elements.append(Paragraph(f"<b>{nome} {cognome}</b>", title_style))
    elements.append(Paragraph(f"Codice Fiscale: {codice_fiscale}", normal_style))
    elements.append(Paragraph(f"Unità Organizzativa: {unita_org}", normal_style))
    elements.append(Paragraph("<br/>", normal_style))
    elements.append(Paragraph(f"ha partecipato al corso", normal_style))
    elements.append(Paragraph("<br/>", normal_style))
    elements.append(Paragraph(f"<b>\"{titolo_corso}\"</b>", title_style))
    elements.append(Paragraph("<br/>", normal_style))
    
    # Add course details
    if progetto and progetto != "N/A":
        elements.append(Paragraph(f"nell'ambito del progetto <b>{progetto}</b>", normal_style))
    
    elements.append(Paragraph("<br/>", normal_style))
    elements.append(Paragraph(f"Modalità: <b>{modalita}</b>", normal_style))
    elements.append(Paragraph("<br/>", normal_style))
    
    # Add attendance and evaluation
    elements.append(Paragraph(f"per un totale di <b>{ore_frequentate}</b> ore complessive", normal_style))
    elements.append(Paragraph(f"con valutazione finale: <b>{valutazione}</b>", normal_style))
    
    # Add date and signature
    elements.append(Paragraph("<br/><br/><br/>", normal_style))
    today = datetime.now().strftime("%d/%m/%Y")
    elements.append(Paragraph(f"Data: {today}", normal_style))
    elements.append(Paragraph("<br/><br/>", normal_style))
    elements.append(Paragraph("Il Responsabile del Corso", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save the PDF to a file
    with open(file_path, 'wb') as f:
        f.write(pdf_data)
    
    return file_path
# Add this route after the admin_attestati route
@app.route('/admin/attestati/<int:attestato_id>/elimina', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_elimina_attestato(attestato_id):
    attestato = Attestato.query.filter_by(id=attestato_id).first_or_404()
    
    try:
        # Delete the file if it exists
        if attestato.file_path and os.path.exists(attestato.file_path):
            os.remove(attestato.file_path)
        
        # Delete the database record
        db.session.delete(attestato)
        db.session.commit()
        
        flash('Attestato eliminato con successo', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
    
    return redirect(url_for('admin_attestati'))

@app.route('/download/attestato/<int:attestato_id>')
@login_required
def download_attestato(attestato_id):
    attestato = Attestato.query.filter_by(id=attestato_id).first_or_404()
    
    # Check permissions
    iscrizione = db.session.get(Iscrizione, attestato.iscrizione_id)
    if not iscrizione:
        abort(404)
        
    # Admin can download any attestato
    # Discenti can only download their own attestati
    if current_user.role != 'admin' and current_user.id != iscrizione.discente_id:
        abort(403)
    
    if not attestato.file_path or not os.path.exists(attestato.file_path):
        flash('File non trovato', 'danger')
        return redirect(url_for('dashboard'))
    
    directory = os.path.dirname(attestato.file_path)
    filename = os.path.basename(attestato.file_path)
    
    return send_from_directory(directory, filename, as_attachment=True)

# Add this new function to automatically check and generate attestati
# Add this route after the admin_nuovo_attestato route

@app.route('/admin/attestati/genera-automatici')
@login_required
@role_required(['admin'])
def admin_genera_attestati_automatici():
    # Find all eligible iscrizioni for attestati
    iscrizioni_eligible = []
    
    # Get all iscrizioni
    iscrizioni = Iscrizione.query.all()
    
    # Track results
    generati = 0
    saltati = 0
    errori = []
    
    for iscrizione in iscrizioni:
        try:
            # Skip if attestato already exists
            existing_attestato = Attestato.query.filter_by(iscrizione_id=iscrizione.id).first()
            if existing_attestato:
                saltati += 1
                continue
            
            # Get related data
            discente = User.query.get_or_404(iscrizione.discente_id)
            corso = Corso.query.get_or_404(iscrizione.corso_id)
            
            # Check if the discente has completed all course hours
            if iscrizione.ore_frequentate < corso.ore_totali:
                saltati += 1
                continue
            
            # Check if the discente has passed the final test
            test_finale = Test.query.filter_by(corso_id=corso.id, tipo='finale').first()
            if test_finale:
                risultato = RisultatoTest.query.filter_by(
                    test_id=test_finale.id,
                    iscrizione_id=iscrizione.id
                ).first()
                
                if not risultato or not risultato.superato or risultato.punteggio < 85:
                    saltati += 1
                    continue
                    
                valutazione = f"{risultato.punteggio}/100"
            else:
                # If no final test exists, we'll use N/A for valutazione
                valutazione = "N/A"
            
            # Generate PDF attestato
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"attestato_{discente.cognome}_{discente.nome}_{timestamp}.pdf"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'attestati', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Generate the PDF
            generate_attestato_pdf(
                file_path,
                discente.nome,
                discente.cognome,
                discente.codice_fiscale or "N/A",
                discente.unita_org or "N/A",
                corso.titolo,
                f"{iscrizione.ore_frequentate}/{corso.ore_totali}",
                valutazione,
                corso.progetto.titolo if corso.progetto else "N/A",
                corso.modalita
            )
            
            # Create attestato record
            attestato = Attestato(
                iscrizione_id=iscrizione.id,
                corso_id=corso.id,  # Aggiungiamo il corso_id
                file_path=file_path,
                data_generazione=datetime.utcnow()
            )
            
            db.session.add(attestato)
            generati += 1
            
        except Exception as e:
            errori.append(f"Errore per iscrizione {iscrizione.id}: {str(e)}")
    
    # Commit all changes at once
    if generati > 0:
        db.session.commit()
    
    # Flash appropriate messages
    if generati > 0:
        flash(f'Generati {generati} attestati automaticamente', 'success')
    if saltati > 0:
        flash(f'Saltati {saltati} iscrizioni non idonee', 'info')
    if errori:
        for errore in errori[:5]:  # Show only first 5 errors
            flash(errore, 'danger')
        if len(errori) > 5:
            flash(f'... e altri {len(errori) - 5} errori', 'danger')
    
    return redirect(url_for('admin_attestati'))

@app.route('/admin/report/progetto')
@login_required
@role_required(['admin'])
def admin_report_progetto():
    progetto_id = request.args.get('progetto_id', type=int)
    if not progetto_id:
        flash('Seleziona un progetto', 'danger')
        return redirect(url_for('admin_report'))
        
    progetto = Progetto.query.filter_by(id=progetto_id).first_or_404()
    corsi = Corso.query.filter_by(progetto_id=progetto_id).all()
    return render_template('admin/report_progetto.html', progetto=progetto, corsi=corsi)

@app.route('/admin/report/corso')
@login_required
@role_required(['admin'])
def admin_report_corso():
    corso_id = request.args.get('corso_id', type=int)
    if not corso_id:
        flash('Seleziona un corso', 'danger')
        return redirect(url_for('admin_report'))
        
    corso = Corso.query.get_or_404(corso_id)
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    
    # Recupera i test associati al corso
    tests = Test.query.filter_by(corso_id=corso_id).all()
    
    # Crea un dizionario per memorizzare i risultati dei test per ogni iscrizione
    risultati_test = {}
    for iscrizione in iscrizioni:
        risultati_test[iscrizione.id] = {}
        for test in tests:
            risultato = RisultatoTest.query.filter_by(
                test_id=test.id,
                iscrizione_id=iscrizione.id
            ).first()
            risultati_test[iscrizione.id][test.id] = risultato
    
    return render_template('admin/report_corso.html', 
                          corso=corso, 
                          iscrizioni=iscrizioni, 
                          tests=tests, 
                          risultati_test=risultati_test)


@app.route('/admin/report/export/excel', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_report_export_excel():
    # Get form data
    tipo_report = request.form.get('tipo_report', 'default')
    id_elemento = request.form.get('id_elemento')
    
    # Create a new Excel workbook
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Create a worksheet
    worksheet = workbook.add_worksheet()
    
    # Create header format
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4CAF50',  # Use bg_color instead of color
        'font_color': 'white',  # Use font_color for text color
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Formattazione celle
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter'
    })
    
    if tipo_report == 'progetti':
        # Report di tutti i progetti
        progetti = Progetto.query.all()
        
        # Intestazioni
        headers = ['ID', 'Titolo', 'Data Inizio', 'Data Fine', 'Budget', 'N. Corsi', 'N. Discenti']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Dati
        for row, progetto in enumerate(progetti, start=1):
            n_corsi = len(progetto.corsi)
            n_discenti = User.query.filter_by(progetto_id=progetto.id, role='discente').count()
            
            worksheet.write(row, 0, progetto.id, cell_format)
            worksheet.write(row, 1, progetto.titolo, cell_format)
            worksheet.write(row, 2, progetto.data_inizio.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 3, progetto.data_fine.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 4, f"€ {progetto.budget:.2f}" if progetto.budget else "N/D", cell_format)
            worksheet.write(row, 5, n_corsi, cell_format)
            worksheet.write(row, 6, n_discenti, cell_format)
        
        filename = "report_progetti.xlsx"
    
    elif tipo_report == 'progetto':
        # Report di un singolo progetto e i suoi corsi
        progetto = db.session.get(Progetto, id_elemento)
        if not progetto:
            abort(404)
        corsi = Corso.query.filter_by(progetto_id=progetto.id).all()
        
        # Intestazioni progetto
        worksheet.merge_range('A1:G1', f"Progetto: {progetto.titolo}", header_format)
        worksheet.write(1, 0, "Data Inizio:", header_format)
        worksheet.write(1, 1, progetto.data_inizio.strftime('%d/%m/%Y'), cell_format)
        worksheet.write(1, 2, "Data Fine:", header_format)
        worksheet.write(1, 3, progetto.data_fine.strftime('%d/%m/%Y'), cell_format)
        worksheet.write(1, 4, "Budget:", header_format)
        worksheet.write(1, 5, f"€ {progetto.budget:.2f}" if progetto.budget else "N/D", cell_format)
        
        # Intestazioni corsi
        headers = ['ID', 'Titolo Corso', 'Ore Totali', 'Data Inizio', 'Data Fine', 'Docente', 'N. Iscritti']
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Dati corsi
        for row, corso in enumerate(corsi, start=4):
            docente = db.session.get(User, corso.docente_id)
            n_iscritti = Iscrizione.query.filter_by(corso_id=corso.id).count()
            
            worksheet.write(row, 0, corso.id, cell_format)
            worksheet.write(row, 1, corso.titolo, cell_format)
            worksheet.write(row, 2, corso.ore_totali, cell_format)
            worksheet.write(row, 3, corso.data_inizio.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 4, corso.data_fine.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 5, f"{docente.nome} {docente.cognome}" if docente else "N/D", cell_format)
            worksheet.write(row, 6, n_iscritti, cell_format)
        
        filename = f"report_progetto_{progetto.id}.xlsx"
    
    elif tipo_report == 'corso':
        # Report di un singolo corso e i suoi discenti
        corso = Corso.query.filter_by(id=id_elemento).first_or_404()
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
        
        # Intestazioni corso
        worksheet.merge_range('A1:G1', f"Corso: {corso.titolo}", header_format)
        worksheet.write(1, 0, "Data Inizio:", header_format)
        worksheet.write(1, 1, corso.data_inizio.strftime('%d/%m/%Y'), cell_format)
        worksheet.write(1, 2, "Data Fine:", header_format)
        worksheet.write(1, 3, corso.data_fine.strftime('%d/%m/%Y'), cell_format)
        worksheet.write(1, 4, "Ore Totali:", header_format)
        worksheet.write(1, 5, corso.ore_totali, cell_format)
        
        docente = db.session.get(User, corso.docente_id)
        worksheet.write(2, 0, "Docente:", header_format)
        worksheet.write(2, 1, f"{docente.nome} {docente.cognome}" if docente else "N/D", cell_format)
        
        # Recupera i test associati al corso
        tests = Test.query.filter_by(corso_id=corso.id).all()
        
        # Intestazioni discenti
        headers = ['ID', 'Nome', 'Cognome', 'Email', 'Codice Fiscale', 'Ore Frequentate', 'Progetto']
        
        # Aggiungi intestazioni per i test
        for test in tests:
            headers.append(f'Test {test.tipo} - {test.titolo}')
            
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # Dati discenti
        for row, iscrizione in enumerate(iscrizioni, start=5):
            discente = db.session.get(User, iscrizione.discente_id)
            progetto = db.session.get(Progetto, discente.progetto_id) if discente.progetto_id else None
            
            worksheet.write(row, 0, discente.id, cell_format)
            worksheet.write(row, 1, discente.nome, cell_format)
            worksheet.write(row, 2, discente.cognome, cell_format)
            worksheet.write(row, 3, discente.email, cell_format)
            worksheet.write(row, 4, discente.codice_fiscale or "N/D", cell_format)
            worksheet.write(row, 5, iscrizione.ore_frequentate, cell_format)
            worksheet.write(row, 6, progetto.titolo if progetto else "N/D", cell_format)
            
            # Aggiungi i risultati dei test
            col_offset = 7
            for i, test in enumerate(tests):
                risultato = RisultatoTest.query.filter_by(
                    test_id=test.id,
                    iscrizione_id=iscrizione.id
                ).first()
                
                if risultato:
                    worksheet.write(row, col_offset + i, f"{risultato.punteggio}%", cell_format)
                else:
                    worksheet.write(row, col_offset + i, "Non sostenuto", cell_format)
        
        filename = f"report_corso_{corso.id}.xlsx"
    
    else:
        # Report di default con tutti i corsi
        corsi = Corso.query.all()
        
        # Intestazioni
        headers = ['ID', 'Titolo', 'Ore Totali', 'Data Inizio', 'Data Fine', 'Docente', 'N. Iscritti']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Dati
        for row, corso in enumerate(corsi, start=1):
            docente = db.session.get(User, corso.docente_id)
            n_iscritti = Iscrizione.query.filter_by(corso_id=corso.id).count()
            
            worksheet.write(row, 0, corso.id, cell_format)
            worksheet.write(row, 1, corso.titolo, cell_format)
            worksheet.write(row, 2, corso.ore_totali, cell_format)
            worksheet.write(row, 3, corso.data_inizio.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 4, corso.data_fine.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 5, f"{docente.nome} {docente.cognome}" if docente else "N/D", cell_format)
            worksheet.write(row, 6, n_iscritti, cell_format)
        
        filename = "report_corsi.xlsx"
    
    # Adatta larghezza colonne
    for i, width in enumerate([10, 40, 15, 15, 15, 25, 15]):
        worksheet.set_column(i, i, width)
    
    # Chiudi il workbook
    workbook.close()
    
    # Prepara la risposta
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return response

@app.route('/admin/report/export/pdf', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_report_export_pdf():
    tipo_report = request.form.get('tipo_report')
    id_elemento = request.form.get('id_elemento')
    
    # Crea un file PDF in memoria
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    elements = []
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    if tipo_report == 'progetti':
        # Report di tutti i progetti
        progetti = Progetto.query.all()
        
        # Titolo
        elements.append(Paragraph("Report Progetti", title_style))
        elements.append(Paragraph(f"Data: {datetime.utcnow().strftime('%d/%m/%Y')}", normal_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        # Tabella
        data = [['ID', 'Titolo', 'Data Inizio', 'Data Fine', 'Budget', 'N. Corsi', 'N. Discenti']]
        
        for progetto in progetti:
            n_corsi = len(progetto.corsi)
            n_discenti = User.query.filter_by(progetto_id=progetto.id, role='discente').count()
            
            data.append([
                str(progetto.id),
                progetto.titolo,
                progetto.data_inizio.strftime('%d/%m/%Y'),
                progetto.data_fine.strftime('%d/%m/%Y'),
                f"€ {progetto.budget:.2f}" if progetto.budget else "N/D",
                str(n_corsi),
                str(n_discenti)
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        filename = "report_progetti.pdf"
    
    elif tipo_report == 'progetto':
        # Report di un singolo progetto e i suoi corsi
        progetto = db.session.get(Progetto, id_elemento)
        if not progetto:
            abort(404)
        corsi = Corso.query.filter_by(progetto_id=progetto.id).all()
        
        # Titolo e info progetto
        elements.append(Paragraph(f"Report Progetto: {progetto.titolo}", title_style))
        elements.append(Paragraph(f"Data: {datetime.utcnow().strftime('%d/%m/%Y')}", normal_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        info_progetto = [
            ['Data Inizio', progetto.data_inizio.strftime('%d/%m/%Y')],
            ['Data Fine', progetto.data_fine.strftime('%d/%m/%Y')],
            ['Budget', f"€ {progetto.budget:.2f}" if progetto.budget else "N/D"]
        ]
        
        table_info = Table(info_progetto)
        table_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table_info)
        elements.append(Paragraph(" ", normal_style))  # Spazio
        elements.append(Paragraph("Corsi del Progetto", subtitle_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        # Tabella corsi
        if corsi:
            data_corsi = [['ID', 'Titolo', 'Ore Totali', 'Data Inizio', 'Data Fine', 'Docente', 'N. Iscritti']]
            
            for corso in corsi:
                docente = db.session.get(User, corso.docente_id)
                n_iscritti = Iscrizione.query.filter_by(corso_id=corso.id).count()
                
                data_corsi.append([
                    str(corso.id),
                    corso.titolo,
                    str(corso.ore_totali),
                    corso.data_inizio.strftime('%d/%m/%Y'),
                    corso.data_fine.strftime('%d/%m/%Y'),
                    f"{docente.nome} {docente.cognome}" if docente else "N/D",
                    str(n_iscritti)
                ])
            
            table_corsi = Table(data_corsi)
            table_corsi.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table_corsi)
        else:
            elements.append(Paragraph("Nessun corso associato a questo progetto.", normal_style))
        
        filename = f"report_progetto_{progetto.id}.pdf"
    
    elif tipo_report == 'corso':
        # Report di un singolo corso e i suoi discenti
        corso = Corso.query.filter_by(id=id_elemento).first_or_404()
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso.id).all()
        
        # Titolo e info corso
        elements.append(Paragraph(f"Report Corso: {corso.titolo}", title_style))
        elements.append(Paragraph(f"Data: {datetime.utcnow().strftime('%d/%m/%Y')}", normal_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        docente = db.session.get(User, corso.docente_id)
        progetto = db.session.get(Progetto, corso.progetto_id) if corso.progetto_id else None
        
        info_corso = [
            ['Data Inizio', corso.data_inizio.strftime('%d/%m/%Y')],
            ['Data Fine', corso.data_fine.strftime('%d/%m/%Y')],
            ['Ore Totali', str(corso.ore_totali)],
            ['Docente', f"{docente.nome} {docente.cognome}" if docente else "N/D"],
            ['Progetto', progetto.titolo if progetto else "N/D"]
        ]
        
        table_info = Table(info_corso)
        table_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table_info)
        elements.append(Paragraph(" ", normal_style))  # Spazio
        elements.append(Paragraph("Discenti Iscritti", subtitle_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        # Tabella discenti
        if iscrizioni:
            data_discenti = [['ID', 'Nome', 'Cognome', 'Email', 'Codice Fiscale', 'Ore Frequentate']]
            
            for iscrizione in iscrizioni:
                discente = db.session.get(User, iscrizione.discente_id)
                
                data_discenti.append([
                    str(discente.id),
                    discente.nome,
                    discente.cognome,
                    discente.email,
                    discente.codice_fiscale or "N/D",
                    str(iscrizione.ore_frequentate)
                ])
            
            table_discenti = Table(data_discenti)
            table_discenti.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table_discenti)
        else:
            elements.append(Paragraph("Nessun discente iscritto a questo corso.", normal_style))
        
        filename = f"report_corso_{corso.id}.pdf"
    
    else:
        # Report di default con tutti i corsi
        corsi = Corso.query.all()
        
        # Titolo
        elements.append(Paragraph("Report Corsi", title_style))
        elements.append(Paragraph(f"Data: {datetime.utcnow().strftime('%d/%m/%Y')}", normal_style))
        elements.append(Paragraph(" ", normal_style))  # Spazio
        
        # Tabella
        data = [['ID', 'Titolo', 'Ore Totali', 'Data Inizio', 'Data Fine', 'Docente', 'N. Iscritti']]
        
        for corso in corsi:
            docente = db.session.get(User, corso.docente_id)
            n_iscritti = Iscrizione.query.filter_by(corso_id=corso.id).count()
            
            data.append([
                str(corso.id),
                corso.titolo,
                str(corso.ore_totali),
                corso.data_inizio.strftime('%d/%m/%Y'),
                corso.data_fine.strftime('%d/%m/%Y'),
                f"{docente.nome} {docente.cognome}" if docente else "N/D",
                str(n_iscritti)
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        filename = "report_corsi.pdf"
    
    # Costruisci il PDF
    doc.build(elements)
    
    # Prepara la risposta
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "application/pdf"
    
    return response

@app.route('/discente/dashboard')
@login_required
@role_required(['discente'])
def discente_dashboard():
    # Get current date for comparisons
    now = datetime.now().date()  # Convertiamo in date per il confronto
    
    # Get user's enrollments
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    
    # Get user's certificates
    attestati = Attestato.query.join(Iscrizione).filter(Iscrizione.discente_id == current_user.id).all()
    
    # Count completed courses
    corsi_completati = sum(1 for i in iscrizioni if i.corso_ref is not None and i.corso_ref.data_fine < now)
    
    return render_template('discente/dashboard.html', 
                          iscrizioni=iscrizioni, 
                          attestati=attestati,
                          corsi_completati=corsi_completati,
                          now=now)
# Rotte per discenti
@app.route('/discente/corsi')
@login_required
@role_required(['discente'])
def discente_corsi():
    # Aggiungi questa riga per definire 'now'
    now = datetime.utcnow()
    
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/corsi.html', iscrizioni=iscrizioni, now=now)

@app.route('/discente/attestati')
@login_required
@role_required(['discente'])
def discente_attestati():
    attestati = Attestato.query.join(Iscrizione).filter(Iscrizione.discente_id == current_user.id).all()
    return render_template('discente/attestati.html', attestati=attestati)

@app.route('/discente/corsi/<int:corso_id>')
@login_required
@role_required(['discente'])
def discente_dettaglio_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    iscrizione = Iscrizione.query.filter_by(corso_id=corso_id, discente_id=current_user.id).first_or_404()
    test = Test.query.filter_by(corso_id=corso_id).all()
    
    # Get test results for this user through the iscrizione
    risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).all()
    risultati_dict = {r.test_id: r for r in risultati}
    
    # Add a helper function to get results for each test
    def get_risultato(test_obj):
        return risultati_dict.get(test_obj.id)
    
    # Add the current datetime for template comparison
    now = datetime.utcnow()
    
    return render_template('discente/dettaglio_corso.html', 
                          corso=corso, 
                          iscrizione=iscrizione,
                          test=test,
                          risultati_dict=risultati_dict,
                          get_risultato=get_risultato,
                          now=now)

@app.route('/discente/corsi/disponibili')
@login_required
@role_required(['discente'])
def discente_corsi_disponibili():
    # Get all courses
    corsi = Corso.query.all()
    
    # Get courses the user is already enrolled in
    iscrizioni_esistenti = [i.corso_id for i in Iscrizione.query.filter_by(discente_id=current_user.id).all()]
    
    # Filter out courses the user is already enrolled in
    corsi_disponibili = [c for c in corsi if c.id not in iscrizioni_esistenti]
    
    now = datetime.utcnow()
    
    return render_template('discente/corsi_disponibili.html', 
                          corsi=corsi_disponibili,
                          now=now)

@app.route('/discente/corsi/<int:corso_id>/iscrizione', methods=['POST'])
@login_required
@role_required(['discente'])
def discente_iscrizione_corso(corso_id):
    # Check if course exists
    corso = Corso.query.get_or_404(corso_id)
    
    # Check if user is already enrolled
    iscrizione_esistente = Iscrizione.query.filter_by(corso_id=corso_id, discente_id=current_user.id).first()
    if iscrizione_esistente:
        flash('Sei già iscritto a questo corso', 'warning')
        return redirect(url_for('discente_corsi_disponibili'))
    
    # Create new enrollment
    iscrizione = Iscrizione(
        discente_id=current_user.id,
        corso_id=corso_id,
        ore_frequentate=0
    )
    
    db.session.add(iscrizione)
    db.session.commit()
    
    flash('Iscrizione effettuata con successo', 'success')
    return redirect(url_for('discente_dashboard'))

@app.route('/discente/test/<int:test_id>/risultato')
@login_required
@role_required(['discente'])
def discente_visualizza_risultato(test_id):
    # Get the test
    test = Test.query.filter_by(id=test_id).first_or_404()
    
    # Get the enrollment for this course
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=test.corso_id
    ).first_or_404()
    
    # Get the test result
    risultato = RisultatoTest.query.filter_by(
        test_id=test_id,
        iscrizione_id=iscrizione.id
    ).first_or_404()
    
    return render_template('discente/risultato_test.html', 
                          test=test, 
                          risultato=risultato,
                          corso=test.corso)

@app.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
    if request.method == 'POST':
        # Update user information
        current_user.nome = request.form.get('nome')
        current_user.cognome = request.form.get('cognome')
        current_user.email = request.form.get('email')
        
        # Check if password is being updated
        password = request.form.get('password')
        if password and password.strip():
            current_user.set_password(password)
        
        db.session.commit()
        flash('Profilo aggiornato con successo', 'success')
        return redirect(url_for('profilo'))
    
    return render_template('profilo.html')


# Gestione errori
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.route('/setup-templates')
def setup_templates():
    # Create directories if they don't exist
    for dir_path in [
        'templates',
        'templates/admin',
        'templates/docente',
        'templates/discente',
        'templates/errors',
        'static',
        'static/css',
        'static/js',
        'static/img',
        'uploads'
    ]:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
    
    # Create a simple base template
    with open(os.path.join(os.path.dirname(__file__), 'templates/base.html'), 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Gestione Corsi PNRR{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Gestione Corsi PNRR</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    {% if current_user.is_authenticated %}
                        {% if current_user.role == 'admin' %}
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin_dashboard') }}">Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin_utenti') }}">Utenti</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin_corsi') }}">Corsi</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin_test') }}">Test</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin_attestati') }}">Attestati</a>
                            </li>
                        {% elif current_user.role == 'docente' %}
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('docente_dashboard') }}">Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('docente_corsi') }}">Corsi</a>
                            </li>
                        {% else %}
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('discente_dashboard') }}">Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('discente_corsi') }}">Corsi</a>
                            </li>
                        {% endif %}
                    {% endif %}
                </ul>
                <ul class="navbar-nav">
                    {% if current_user.is_authenticated %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('login') }}">Login</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>''')
    
    # Create login template
    with open(os.path.join(os.path.dirname(__file__), 'templates/login.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Login - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3 class="text-center">Login</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Accedi</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create admin dashboard template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard Amministratore - Gestione Corsi PNRR{% endblock %}

{% block content %}
<h1 class="mb-4">Dashboard Amministratore</h1>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Discenti</h5>
                <p class="card-text display-4">{{ discenti_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Corsi</h5>
                <p class="card-text display-4">{{ corsi_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Test Completati</h5>
                <p class="card-text display-4">{{ test_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5 class="card-title">Attestati</h5>
                <p class="card-text display-4">{{ attestati_count }}</p>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Corsi Recenti</h5>
        <a href="{{ url_for('admin_corsi') }}" class="btn btn-sm btn-primary">Vedi Tutti</a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Titolo</th>
                        <th>Docente</th>
                        <th>Data Inizio</th>
                        <th>Data Fine</th>
                        <th>Iscritti</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% if corsi %}
                        {% for corso in corsi %}
                        <tr>
                            <td>{{ corso.titolo }}</td>
                            <td>{{ corso.docente.nome }} {{ corso.docente.cognome }}</td>
                            <td>{{ corso.data_inizio.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.data_fine.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.iscrizioni|length }}</td>
                            <td>
                                {% if corso.data_inizio > now %}
                                    <span class="badge bg-warning">In Programma</span>
                                {% elif corso.data_fine < now %}
                                    <span class="badge bg-success">Completato</span>
                                {% else %}
                                    <span class="badge bg-primary">In Corso</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('admin_dettaglio_corso', corso_id=corso.id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7" class="text-center">Nessun corso disponibile</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create admin users template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/utenti.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Gestione Utenti - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Gestione Utenti</h1>
    <a href="{{ url_for('admin_nuovo_utente') }}" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> Nuovo Utente
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Nome</th>
                        <th>Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for utente in utenti %}
                    <tr>
                        <td>{{ utente.id }}</td>
                        <td>{{ utente.username }}</td>
                        <td>{{ utente.nome }}</td>
                        <td>{{ utente.cognome }}</td>
                        <td>{{ utente.email }}</td>
                        <td>
                            {% if utente.role == 'admin' %}
                                <span class="badge bg-danger">Amministratore</span>
                            {% elif utente.role == 'docente' %}
                                <span class="badge bg-primary">Docente</span>
                            {% else %}
                                <span class="badge bg-success">Discente</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="#" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="#" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create new user form
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create login template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create admin dashboard template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard Amministratore - Gestione Corsi PNRR{% endblock %}

{% block content %}
<h1 class="mb-4">Dashboard Amministratore</h1>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Discenti</h5>
                <p class="card-text display-4">{{ discenti_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Corsi</h5>
                <p class="card-text display-4">{{ corsi_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Test Completati</h5>
                <p class="card-text display-4">{{ test_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5 class="card-title">Attestati</h5>
                <p class="card-text display-4">{{ attestati_count }}</p>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Corsi Recenti</h5>
        <a href="{{ url_for('admin_corsi') }}" class="btn btn-sm btn-primary">Vedi Tutti</a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Titolo</th>
                        <th>Docente</th>
                        <th>Data Inizio</th>
                        <th>Data Fine</th>
                        <th>Iscritti</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% if corsi %}
                        {% for corso in corsi %}
                        <tr>
                            <td>{{ corso.titolo }}</td>
                            <td>{{ corso.docente.nome }} {{ corso.docente.cognome }}</td>
                            <td>{{ corso.data_inizio.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.data_fine.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.iscrizioni|length }}</td>
                            <td>
                                {% if corso.data_inizio > now %}
                                    <span class="badge bg-warning">In Programma</span>
                                {% elif corso.data_fine < now %}
                                    <span class="badge bg-success">Completato</span>
                                {% else %}
                                    <span class="badge bg-primary">In Corso</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('admin_dettaglio_corso', corso_id=corso.id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7" class="text-center">Nessun corso disponibile</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create admin users template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/utenti.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Gestione Utenti - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Gestione Utenti</h1>
    <a href="{{ url_for('admin_nuovo_utente') }}" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> Nuovo Utente
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Nome</th>
                        <th>Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for utente in utenti %}
                    <tr>
                        <td>{{ utente.id }}</td>
                        <td>{{ utente.username }}</td>
                        <td>{{ utente.nome }}</td>
                        <td>{{ utente.cognome }}</td>
                        <td>{{ utente.email }}</td>
                        <td>
                            {% if utente.role == 'admin' %}
                                <span class="badge bg-danger">Amministratore</span>
                            {% elif utente.role == 'docente' %}
                                <span class="badge bg-primary">Docente</span>
                            {% else %}
                                <span class="badge bg-success">Discente</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="#" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="#" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create new user form
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create login template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create admin dashboard template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard Amministratore - Gestione Corsi PNRR{% endblock %}

{% block content %}
<h1 class="mb-4">Dashboard Amministratore</h1>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Discenti</h5>
                <p class="card-text display-4">{{ discenti_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Corsi</h5>
                <p class="card-text display-4">{{ corsi_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Test Completati</h5>
                <p class="card-text display-4">{{ test_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5 class="card-title">Attestati</h5>
                <p class="card-text display-4">{{ attestati_count }}</p>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Corsi Recenti</h5>
        <a href="{{ url_for('admin_corsi') }}" class="btn btn-sm btn-primary">Vedi Tutti</a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Titolo</th>
                        <th>Docente</th>
                        <th>Data Inizio</th>
                        <th>Data Fine</th>
                        <th>Iscritti</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% if corsi %}
                        {% for corso in corsi %}
                        <tr>
                            <td>{{ corso.titolo }}</td>
                            <td>{{ corso.docente.nome }} {{ corso.docente.cognome }}</td>
                            <td>{{ corso.data_inizio.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.data_fine.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.iscrizioni|length }}</td>
                            <td>
                                {% if corso.data_inizio > now %}
                                    <span class="badge bg-warning">In Programma</span>
                                {% elif corso.data_fine < now %}
                                    <span class="badge bg-success">Completato</span>
                                {% else %}
                                    <span class="badge bg-primary">In Corso</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('admin_dettaglio_corso', corso_id=corso.id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7" class="text-center">Nessun corso disponibile</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create admin users template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/utenti.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Gestione Utenti - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Gestione Utenti</h1>
    <a href="{{ url_for('admin_nuovo_utente') }}" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> Nuovo Utente
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Nome</th>
                        <th>Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for utente in utenti %}
                    <tr>
                        <td>{{ utente.id }}</td>
                        <td>{{ utente.username }}</td>
                        <td>{{ utente.nome }}</td>
                        <td>{{ utente.cognome }}</td>
                        <td>{{ utente.email }}</td>
                        <td>
                            {% if utente.role == 'admin' %}
                                <span class="badge bg-danger">Amministratore</span>
                            {% elif utente.role == 'docente' %}
                                <span class="badge bg-primary">Docente</span>
                            {% else %}
                                <span class="badge bg-success">Discente</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="#" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="#" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create new user form
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create login template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create admin dashboard template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard Amministratore - Gestione Corsi PNRR{% endblock %}

{% block content %}
<h1 class="mb-4">Dashboard Amministratore</h1>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Discenti</h5>
                <p class="card-text display-4">{{ discenti_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Corsi</h5>
                <p class="card-text display-4">{{ corsi_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Test Completati</h5>
                <p class="card-text display-4">{{ test_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5 class="card-title">Attestati</h5>
                <p class="card-text display-4">{{ attestati_count }}</p>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Corsi Recenti</h5>
        <a href="{{ url_for('admin_corsi') }}" class="btn btn-sm btn-primary">Vedi Tutti</a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Titolo</th>
                        <th>Docente</th>
                        <th>Data Inizio</th>
                        <th>Data Fine</th>
                        <th>Iscritti</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% if corsi %}
                        {% for corso in corsi %}
                        <tr>
                            <td>{{ corso.titolo }}</td>
                            <td>{{ corso.docente.nome }} {{ corso.docente.cognome }}</td>
                            <td>{{ corso.data_inizio.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.data_fine.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.iscrizioni|length }}</td>
                            <td>
                                {% if corso.data_inizio > now %}
                                    <span class="badge bg-warning">In Programma</span>
                                {% elif corso.data_fine < now %}
                                    <span class="badge bg-success">Completato</span>
                                {% else %}
                                    <span class="badge bg-primary">In Corso</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('admin_dettaglio_corso', corso_id=corso.id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7" class="text-center">Nessun corso disponibile</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create admin users template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/utenti.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Gestione Utenti - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Gestione Utenti</h1>
    <a href="{{ url_for('admin_nuovo_utente') }}" class="btn btn-primary">
        <i class="bi bi-plus-lg"></i> Nuovo Utente
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Nome</th>
                        <th>Cognome</th>
                        <th>Email</th>
                        <th>Ruolo</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for utente in utenti %}
                    <tr>
                        <td>{{ utente.id }}</td>
                        <td>{{ utente.username }}</td>
                        <td>{{ utente.nome }}</td>
                        <td>{{ utente.cognome }}</td>
                        <td>{{ utente.email }}</td>
                        <td>
                            {% if utente.role == 'admin' %}
                                <span class="badge bg-danger">Amministratore</span>
                            {% elif utente.role == 'docente' %}
                                <span class="badge bg-primary">Docente</span>
                            {% else %}
                                <span class="badge bg-success">Discente</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="#" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="#" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create new user form
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create login template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/nuovo_utente.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Nuovo Utente - Gestione Corsi PNRR{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Nuovo Utente</h1>
    <a href="{{ url_for('admin_utenti') }}" class="btn btn-secondary">
        <i class="bi bi-arrow-left"></i> Torna alla lista
    </a>
</div>

<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username"
                        <label for="email" class="form-label">Email</label>
                        <input type="text" class="form-control" id="email" name="email"
                        <label for="nome" class="form-label">Nome</label>
                        <input type="text" class="form-control" id="nome" name="nome"
                        <label for="cognome" class="form-label">Cognome</label>
                        <input type="text" class="form-control" id="cognome" name="cognome"
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password"
                        <label for="role" class="form-label">Ruolo</label>
                        <input type="text" class="form-control" id="role" name="role"
                        <button type="submit" class="btn btn-primary">Crea Utente</button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}''')
    
    # Create admin dashboard template
    with open(os.path.join(os.path.dirname(__file__), 'templates/admin/dashboard.html'), 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard Amministratore - Gestione Corsi PNRR{% endblock %}

{% block content %}
<h1 class="mb-4">Dashboard Amministratore</h1>

<div class="row">
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Discenti</h5>
                <p class="card-text display-4">{{ discenti_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Corsi</h5>
                <p class="card-text display-4">{{ corsi_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Test Completati</h5>
                <p class="card-text display-4">{{ test_count }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3 mb-4">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5 class="card-title">Attestati</h5>
                <p class="card-text display-4">{{ attestati_count }}</p>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Corsi Recenti</h5>
        <a href="{{ url_for('admin_corsi') }}" class="btn btn-sm btn-primary">Vedi Tutti</a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Titolo</th>
                        <th>Docente</th>
                        <th>Data Inizio</th>
                        <th>Data Fine</th>
                        <th>Iscritti</th>
                        <th>Stato</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% if corsi %}
                        {% for corso in corsi %}
                        <tr>
                            <td>{{ corso.titolo }}</td>
                            <td>{{ corso.docente.nome }} {{ corso.docente.cognome }}</td>
                            <td>{{ corso.data_inizio.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.data_fine.strftime('%d/%m/%Y') }}</td>
                            <td>{{ corso.iscrizioni|length }}</td>
                            <td>
                                {% if corso.data_inizio > now %}
                                    <span class="badge bg-warning">In Programma</span>
                                {% elif corso.data_fine < now %}
                                    <span class="badge bg-success">Completato</span>
                                {% else %}
                                    <span class="badge bg-primary">In Corso</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ url_for('admin_dettaglio_corso', corso_id=corso.id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7" class="text-center">Nessun corso disponibile</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
   
   # Make sure this is at the very end of your file
# Create a dictionary of models to pass to the routes
models = {
    'Progetto': Progetto,
    'Corso': Corso,
    'User': User,
    'Iscrizione': Iscrizione,
    'Test': Test,
    'RisultatoTest': RisultatoTest,
    'Attestato': Attestato
}

# Initialize the routes with the Flask app and other required objects
progetti.init_routes(app, db, role_required, models)

@app.route('/attestati-pubblici/<token>')
def download_attestato_public(token):
    try:
        attestato = Attestato.query.filter_by(public_token=token).first_or_404()
        
        # Verifica che il file esista
        if not os.path.exists(attestato.file_path):
            flash('File non trovato', 'danger')
            return redirect(url_for('index'))
            
        return send_file(
            attestato.file_path,
            as_attachment=True,
            download_name=f"attestato_{attestato.discente.cognome}_{attestato.discente.nome}.pdf"
        )
        
    except Exception as e:
        flash(f'Errore durante il download: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/attestati/genera-csv-badge')
@login_required
@role_required(['admin'])
def genera_csv_badge():
    if current_user.role != 'admin':
        flash('Accesso non autorizzato', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Ottieni tutti gli attestati non ancora esportati
        attestati = Attestato.query.filter_by(badge_exported=False).all()
        
        if not attestati:
            flash('Nessun attestato da esportare', 'warning')
            return redirect(url_for('admin_attestati'))
        
        # Prepara i dati per la visualizzazione
        attestati_data = []
        for attestato in attestati:
            iscrizione = attestato.iscrizione
            discente = iscrizione.discente
            corso = attestato.corso
            
            attestati_data.append({
                'id': attestato.id,
                'discente_nome': f"{discente.cognome} {discente.nome}",
                'discente_email': discente.email,
                'corso_titolo': corso.titolo,
                'data_generazione': attestato.data_generazione.strftime('%d/%m/%Y')
            })
        
        return render_template('admin/genera_csv_badge.html', 
                            attestati=attestati_data,
                            count=len(attestati))
        
    except Exception as e:
        flash(f'Errore durante la preparazione del CSV: {str(e)}', 'danger')
        return redirect(url_for('admin_attestati'))

@app.route('/admin/attestati/export-csv-badge', methods=['POST'])
@login_required
@role_required(['admin'])
def export_csv_badge():
    try:
        # Ottieni tutti gli attestati non ancora esportati
        attestati = Attestato.query.filter_by(badge_exported=False).all()
        
        if not attestati:
            flash('Nessun attestato da esportare', 'warning')
            return redirect(url_for('admin_attestati'))
        
        # Crea il CSV in memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Intestazione del CSV con tutte le colonne richieste
        writer.writerow([
            'Recipient Full Name',
            'First Name',
            'Last Name',
            'Identifier',
            'Name and Email',
            'email',
            'name',
            'evidence_url',
            'badge_name',
            'badge_description'
        ])
        
        # Genera un token unico per ogni attestato e aggiungi i dati al CSV
        for attestato in attestati:
            # Genera un token unico per l'attestato
            token = secrets.token_urlsafe(32)
            attestato.public_token = token
            attestato.badge_exported = True
            
            # Costruisci l'URL pubblico dell'attestato
            evidence_url = url_for('download_attestato_public', token=token, _external=True)
            
            # Ottieni il discente attraverso l'iscrizione
            iscrizione = attestato.iscrizione
            discente = iscrizione.discente
            
            # Aggiungi la riga al CSV con tutte le informazioni richieste
            writer.writerow([
                f"{discente.cognome} {discente.nome}",  # Recipient Full Name
                discente.nome,  # First Name
                discente.cognome,  # Last Name
                discente.codice_fiscale or discente.email,  # Identifier (usiamo il CF o l'email)
                f"{discente.cognome} {discente.nome} <{discente.email}>",  # Name and Email
                discente.email,  # email
                f"{discente.cognome} {discente.nome}",  # name
                evidence_url,  # evidence_url
                f"Attestato {attestato.corso.titolo}",  # badge_name
                f"Attestato di completamento del corso {attestato.corso.titolo}"  # badge_description
            ])
        
        # Salva i cambiamenti nel database
        db.session.commit()
        
        # Prepara il file CSV per il download
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='badges_export.csv'
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la generazione del CSV: {str(e)}', 'danger')
        return redirect(url_for('admin_attestati'))

# ... rest of the code ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea tutte le tabelle se non esistono
    app.run(debug=True)

@app.route('/admin/progetti/crea', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_crea_progetto_post():
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        descrizione = request.form.get('descrizione')
        data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        budget = float(request.form.get('budget', 0))
        link_corso = request.form.get('link_corso')
        
        progetto = Progetto(
            titolo=titolo,
            descrizione=descrizione,
            data_inizio=data_inizio,
            data_fine=data_fine,
            budget=budget,
            link_corso=link_corso
        )
        
        db.session.add(progetto)
        db.session.commit()
        
        flash('Progetto creato con successo', 'success')
        return redirect(url_for('admin_progetti'))
    
    return render_template('admin/nuovo_progetto.html')

@app.cli.command('db-migrate')
def db_migrate():
    """Esegue la migrazione del database"""
    try:
        from migrations.disponibilita import upgrade
        upgrade()
        print("Migrazione completata con successo!")
    except Exception as e:
        print(f"Errore durante la migrazione: {str(e)}")
        
# ...existing code

app.register_blueprint(calendario_bp)


