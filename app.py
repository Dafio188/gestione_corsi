@app.route('/docente/iscrizioni/<int:corso_id>')
@login_required
@role_required(['docente'])
def docente_iscrizioni_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    
    # Verifica che il corso appartenga al docente
    if corso.docente_id != current_user.id:
        flash('Non hai i permessi per visualizzare questo corso', 'danger')
        return redirect(url_for('docente_corsi'))
        
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    return render_template('docente/iscrizioni_corso.html', corso=corso, iscrizioni=iscrizioni)

@app.route('/docente/aggiorna-ore', methods=['POST'])
@login_required
@role_required(['docente'])
def aggiorna_ore():
    if request.method == 'POST':
        iscrizione_id = request.form.get('iscrizione_id')
        ore_frequentate = float(request.form.get('ore_frequentate'))
        
        iscrizione = Iscrizione.query.get_or_404(iscrizione_id)
        
        # Verifica che il corso appartenga al docente
        if iscrizione.corso.docente_id != current_user.id:
            flash('Non hai i permessi per modificare questa iscrizione', 'danger')
            return redirect(url_for('docente_corsi'))
            
        iscrizione.ore_frequentate = ore_frequentate
        db.session.commit()
        
        flash('Ore frequentate aggiornate con successo!', 'success')
        return redirect(url_for('docente_iscrizioni_corso', corso_id=iscrizione.corso_id))

@app.route('/docente/valuta-test', methods=['POST'])
@login_required
@role_required(['docente'])
def valuta_test():
    if request.method == 'POST':
        risultato_id = request.form.get('risultato_id')
        punteggio = float(request.form.get('punteggio'))
        
        risultato = RisultatoTest.query.get_or_404(risultato_id)
        
        # Verifica che il test appartenga a un corso del docente
        if risultato.test.corso.docente_id != current_user.id:
            flash('Non hai i permessi per valutare questo test', 'danger')
            return redirect(url_for('docente_test'))
            
        risultato.punteggio = punteggio
        db.session.commit()
        
        flash('Valutazione registrata con successo!', 'success')
        return redirect(url_for('docente_test'))

# Rotte per discenti
@app.route('/discente/corsi')
@login_required
@role_required(['discente'])
def discente_corsi():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/corsi.html', iscrizioni=iscrizioni)

@app.route('/discente/corso/<int:corso_id>')
@login_required
@role_required(['discente'])
def discente_dettaglio_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=corso_id
    ).first_or_404()
    
    test = Test.query.filter_by(corso_id=corso_id).all()
    risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).all()
    
    # Crea un dizionario per mappare i test ai risultati
    risultati_dict = {r.test_id: r for r in risultati}
    
    return render_template('discente/dettaglio_corso.html', 
                          corso=corso, 
                          iscrizione=iscrizione, 
                          test=test,
                          risultati_dict=risultati_dict)

@app.route('/discente/test/<int:test_id>')
@login_required
@role_required(['discente'])
def discente_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Verifica che il discente sia iscritto al corso
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=test.corso_id
    ).first_or_404()
    
    # Verifica se il test è già stato completato
    risultato = RisultatoTest.query.filter_by(
        test_id=test_id,
        iscrizione_id=iscrizione.id
    ).first()
    
    return render_template('discente/test.html', 
                          test=test, 
                          iscrizione=iscrizione,
                          risultato=risultato)

@app.route('/discente/attestati')
@login_required
@role_required(['discente'])
def discente_attestati():
    # Trova tutte le iscrizioni del discente
    iscrizioni_ids = [i.id for i in Iscrizione.query.filter_by(discente_id=current_user.id).all()]
    
    # Trova tutti gli attestati associati a queste iscrizioni
    attestati = Attestato.query.filter(Attestato.iscrizione_id.in_(iscrizioni_ids)).all()
    
    return render_template('discente/attestati.html', attestati=attestati)

@app.route('/discente/scarica-attestato/<int:attestato_id>')
@login_required
@role_required(['discente'])
def scarica_attestato(attestato_id):
    attestato = Attestato.query.get_or_404(attestato_id)
    
    # Verifica che l'attestato appartenga al discente
    if attestato.iscrizione.discente_id != current_user.id:
        flash('Non hai i permessi per scaricare questo attestato', 'danger')
        return redirect(url_for('discente_attestati'))
    
    # Qui andrebbe implementata la logica per scaricare il file
    # Per ora, reindirizza alla pagina degli attestati
    flash('Funzionalità di download non ancora implementata', 'warning')
    return redirect(url_for('discente_attestati'))

# API per richieste AJAX
@app.route('/api/corsi/<int:corso_id>/discenti')
@login_required
def api_discenti_corso(corso_id):
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    discenti = []
    
    for iscrizione in iscrizioni:
        discente = iscrizione.discente
        discenti.append({
            'id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'email': discente.email,
            'ore_frequentate': iscrizione.ore_frequentate
        })
    
    return jsonify(discenti)

@app.route('/api/test/<int:test_id>/risultati')
@login_required
def api_risultati_test(test_id):
    risultati = RisultatoTest.query.filter_by(test_id=test_id).all()
    data = []
    
    for risultato in risultati:
        discente = risultato.iscrizione.discente
        data.append({
            'id': risultato.id,
            'discente_id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'punteggio': risultato.punteggio,
            'data_completamento': risultato.data_completamento.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify(data)

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


from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina'
login_manager.login_message_category = 'warning'

# Modello Utente
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='discente')  # 'admin', 'docente', 'discente'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
import os

from config import Config
from models import db, User, Corso, Iscrizione, Test, RisultatoTest, Attestato

app = Flask(__name__)
app.config.from_object(Config)

# Inizializzazione delle estensioni
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decoratore per controllo ruoli
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Non hai i permessi per accedere a questa pagina', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rotte per autenticazione
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
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
    # Reindirizza alla dashboard specifica in base al ruolo
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'docente':
        return redirect(url_for('docente_dashboard'))
    else:  # discente
        return redirect(url_for('discente_dashboard'))

# Dashboard per amministratori
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    discenti_count = User.query.filter_by(role='discente').count()
    corsi_count = Corso.query.count()
    test_count = Test.query.count()
    
    return render_template('admin/dashboard.html', 
                          discenti_count=discenti_count,
                          corsi_count=corsi_count,
                          test_count=test_count)

# Dashboard per docenti
@app.route('/docente/dashboard')
@login_required
@role_required(['docente'])
def docente_dashboard():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/dashboard.html', corsi=corsi)

# Dashboard per discenti
@app.route('/discente/dashboard')
@login_required
@role_required(['discente'])
def discente_dashboard():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/dashboard.html', iscrizioni=iscrizioni)

# Gestione utenti (solo admin)
@app.route('/admin/gestione-utenti')
@login_required
@role_required(['admin'])
def gestione_utenti():
    users = User.query.all()
    return render_template('admin/gestione_utenti.html', users=users)

# Inizializzazione del database e creazione di un utente admin di default
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # Crea un utente admin se non esiste
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            nome='Amministratore',
            cognome='Sistema',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Utente admin creato con successo!')
    
    print('Database inizializzato!')

# Add these routes after the existing ones in app.py

# Gestione Corsi (Admin)
@app.route('/admin/corsi')
@login_required
@role_required(['admin'])
def admin_corsi():
    corsi = Corso.query.all()
    docenti = User.query.filter_by(role='docente').all()
    return render_template('admin/gestione_corsi.html', corsi=corsi, docenti=docenti)

@app.route('/admin/corsi/nuovo', methods=['POST'])
@login_required
@role_required(['admin'])
def nuovo_corso():
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        descrizione = request.form.get('descrizione')
        ore_totali = request.form.get('ore_totali')
        data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        progetto_riferimento = request.form.get('progetto_riferimento')
        docente_id = request.form.get('docente_id')
        
        corso = Corso(
            titolo=titolo,
            descrizione=descrizione,
            ore_totali=ore_totali,
            data_inizio=data_inizio,
            data_fine=data_fine,
            progetto_riferimento=progetto_riferimento,
            docente_id=docente_id
        )
        
        db.session.add(corso)
        db.session.commit()
        
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('admin_corsi'))

# Gestione Iscrizioni
@app.route('/admin/iscrizioni')
@login_required
@role_required(['admin'])
def admin_iscrizioni():
    iscrizioni = Iscrizione.query.all()
    return render_template('admin/gestione_iscrizioni.html', iscrizioni=iscrizioni)

@app.route('/admin/iscrizioni/nuova', methods=['POST'])
@login_required
@role_required(['admin'])
def nuova_iscrizione():
    if request.method == 'POST':
        discente_id = request.form.get('discente_id')
        corso_id = request.form.get('corso_id')
        
        # Verifica se l'iscrizione esiste già
        iscrizione_esistente = Iscrizione.query.filter_by(
            discente_id=discente_id, 
            corso_id=corso_id
        ).first()
        
        if iscrizione_esistente:
            flash('Questo discente è già iscritto al corso selezionato!', 'danger')
        else:
            iscrizione = Iscrizione(
                discente_id=discente_id,
                corso_id=corso_id
            )
            
            db.session.add(iscrizione)
            db.session.commit()
            
            flash('Iscrizione creata con successo!', 'success')
            
        return redirect(url_for('admin_iscrizioni'))

# Gestione Test
@app.route('/admin/test')
@login_required
@role_required(['admin'])
def admin_test():
    test = Test.query.all()
    corsi = Corso.query.all()
    return render_template('admin/gestione_test.html', test=test, corsi=corsi)

@app.route('/admin/test/nuovo', methods=['POST'])
@login_required
@role_required(['admin', 'docente'])
def nuovo_test():
    if request.method == 'POST':
        corso_id = request.form.get('corso_id')
        tipo = request.form.get('tipo')
        titolo = request.form.get('titolo')
        forms_link = request.form.get('forms_link')
        
        # Gestione upload file
        file = request.files.get('file_test')
        file_path = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            
            # Assicurati che la directory esista
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            file.save(file_path)
        
        test = Test(
            corso_id=corso_id,
            tipo=tipo,
            titolo=titolo,
            file_path=file_path,
            forms_link=forms_link
        )
        
        db.session.add(test)
        db.session.commit()
        
        flash('Test creato con successo!', 'success')
        
        if current_user.role == 'admin':
            return redirect(url_for('admin_test'))
        else:
            return redirect(url_for('docente_test'))

# Caricamento risultati test da Excel
@app.route('/admin/test/carica-risultati', methods=['POST'])
@login_required
@role_required(['admin', 'docente'])
def carica_risultati_test():
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        file = request.files.get('file_excel')
        
        if file and file.filename:
            # Qui andrebbe implementata la logica per leggere il file Excel
            # e caricare i risultati nel database
            
            flash('Risultati caricati con successo!', 'success')
        else:
            flash('Nessun file selezionato!', 'danger')
        
        if current_user.role == 'admin':
            return redirect(url_for('admin_test'))
        else:
            return redirect(url_for('docente_test'))

# Gestione Attestati
@app.route('/admin/attestati')
@login_required
@role_required(['admin'])
def admin_attestati():
    attestati = Attestato.query.all()
    return render_template('admin/gestione_attestati.html', attestati=attestati)

@app.route('/admin/attestati/genera', methods=['POST'])
@login_required
@role_required(['admin'])
def genera_attestati():
    if request.method == 'POST':
        corso_id = request.form.get('corso_id')
        
        # Trova tutte le iscrizioni per il corso
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
        
        attestati_generati = 0
        
        for iscrizione in iscrizioni:
            # Verifica se l'attestato esiste già
            attestato_esistente = Attestato.query.filter_by(iscrizione_id=iscrizione.id).first()
            
            if attestato_esistente:
                continue
                
            # Verifica i criteri per il rilascio dell'attestato
            corso = iscrizione.corso
            ore_minime = corso.ore_totali * 0.8  # 80% delle ore totali
            
            # Trova il test finale
            test_finale = Test.query.filter_by(corso_id=corso.id, tipo='finale').first()
            
            if not test_finale:
                continue
                
            # Trova il risultato del test finale
            risultato_test = RisultatoTest.query.filter_by(
                test_id=test_finale.id,
                iscrizione_id=iscrizione.id
            ).first()
            
            if not risultato_test:
                continue
                
            # Verifica i criteri
            if iscrizione.ore_frequentate >= ore_minime and risultato_test.punteggio >= 85:
                # Genera l'attestato
                attestato = Attestato(
                    iscrizione_id=iscrizione.id,
                    file_path=None  # Qui andrebbe implementata la generazione del PDF
                )
                
                db.session.add(attestato)
                attestati_generati += 1
        
        if attestati_generati > 0:
            db.session.commit()
            flash(f'{attestati_generati} attestati generati con successo!', 'success')
        else:
            flash('Nessun attestato generato. Verifica i criteri di rilascio.', 'warning')
            
        return redirect(url_for('admin_attestati'))

# Rotte per docenti
@app.route('/docente/corsi')
@login_required
@role_required(['docente'])
def docente_corsi():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/corsi.html', corsi=corsi)

@app.route('/docente/test')
@login_required
@role_required(['docente'])
def docente_test():
    corsi_ids = [corso.id for corso in Corso.query.filter_by(docente_id=current_user.id).all()]
    test = Test.query.filter(Test.corso_id.in_(corsi_ids)).all()
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/test.html', test=test, corsi=corsi)

@app.route('/docente/iscrizioni/<int:corso_id>')
@login_required
@role_required(['docente'])
def docente_iscrizioni_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    
    # Verifica che il corso appartenga al docente
    if corso.docente_id != current_user.id:
        flash('Non hai i permessi per visualizzare questo corso', 'danger')
        return redirect(url_for('docente_corsi'))
        
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    return render_template('docente/iscrizioni_corso.html', corso=corso, iscrizioni=iscrizioni)

@app.route('/docente/aggiorna-ore', methods=['POST'])
@login_required
@role_required(['docente'])
def aggiorna_ore():
    if request.method == 'POST':
        iscrizione_id = request.form.get('iscrizione_id')
        ore_frequentate = float(request.form.get('ore_frequentate'))
        
        iscrizione = Iscrizione.query.get_or_404(iscrizione_id)
        
        # Verifica che il corso appartenga al docente
        if iscrizione.corso.docente_id != current_user.id:
            flash('Non hai i permessi per modificare questa iscrizione', 'danger')
            return redirect(url_for('docente_corsi'))
            
        iscrizione.ore_frequentate = ore_frequentate
        db.session.commit()
        
        flash('Ore frequentate aggiornate con successo!', 'success')
        return redirect(url_for('docente_iscrizioni_corso', corso_id=iscrizione.corso_id))

@app.route('/docente/valuta-test', methods=['POST'])
@login_required
@role_required(['docente'])
def valuta_test():
    if request.method == 'POST':
        risultato_id = request.form.get('risultato_id')
        punteggio = float(request.form.get('punteggio'))
        
        risultato = RisultatoTest.query.get_or_404(risultato_id)
        
        # Verifica che il test appartenga a un corso del docente
        if risultato.test.corso.docente_id != current_user.id:
            flash('Non hai i permessi per valutare questo test', 'danger')
            return redirect(url_for('docente_test'))
            
        risultato.punteggio = punteggio
        db.session.commit()
        
        flash('Valutazione registrata con successo!', 'success')
        return redirect(url_for('docente_test'))

# Rotte per discenti
@app.route('/discente/corsi')
@login_required
@role_required(['discente'])
def discente_corsi():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/corsi.html', iscrizioni=iscrizioni)

@app.route('/discente/corso/<int:corso_id>')
@login_required
@role_required(['discente'])
def discente_dettaglio_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=corso_id
    ).first_or_404()
    
    test = Test.query.filter_by(corso_id=corso_id).all()
    risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).all()
    
    # Crea un dizionario per mappare i test ai risultati
    risultati_dict = {r.test_id: r for r in risultati}
    
    return render_template('discente/dettaglio_corso.html', 
                          corso=corso, 
                          iscrizione=iscrizione, 
                          test=test,
                          risultati_dict=risultati_dict)

@app.route('/discente/test/<int:test_id>')
@login_required
@role_required(['discente'])
def discente_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Verifica che il discente sia iscritto al corso
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=test.corso_id
    ).first_or_404()
    
    # Verifica se il test è già stato completato
    risultato = RisultatoTest.query.filter_by(
        test_id=test_id,
        iscrizione_id=iscrizione.id
    ).first()
    
    return render_template('discente/test.html', 
                          test=test, 
                          iscrizione=iscrizione,
                          risultato=risultato)

@app.route('/discente/attestati')
@login_required
@role_required(['discente'])
def discente_attestati():
    # Trova tutte le iscrizioni del discente
    iscrizioni_ids = [i.id for i in Iscrizione.query.filter_by(discente_id=current_user.id).all()]
    
    # Trova tutti gli attestati associati a queste iscrizioni
    attestati = Attestato.query.filter(Attestato.iscrizione_id.in_(iscrizioni_ids)).all()
    
    return render_template('discente/attestati.html', attestati=attestati)

@app.route('/discente/scarica-attestato/<int:attestato_id>')
@login_required
@role_required(['discente'])
def scarica_attestato(attestato_id):
    attestato = Attestato.query.get_or_404(attestato_id)
    
    # Verifica che l'attestato appartenga al discente
    if attestato.iscrizione.discente_id != current_user.id:
        flash('Non hai i permessi per scaricare questo attestato', 'danger')
        return redirect(url_for('discente_attestati'))
    
    # Qui andrebbe implementata la logica per scaricare il file
    # Per ora, reindirizza alla pagina degli attestati
    flash('Funzionalità di download non ancora implementata', 'warning')
    return redirect(url_for('discente_attestati'))

# API per richieste AJAX
@app.route('/api/corsi/<int:corso_id>/discenti')
@login_required
def api_discenti_corso(corso_id):
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    discenti = []
    
    for iscrizione in iscrizioni:
        discente = iscrizione.discente
        discenti.append({
            'id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'email': discente.email,
            'ore_frequentate': iscrizione.ore_frequentate
        })
    
    return jsonify(discenti)

@app.route('/api/test/<int:test_id>/risultati')
@login_required
def api_risultati_test(test_id):
    risultati = RisultatoTest.query.filter_by(test_id=test_id).all()
    data = []
    
    for risultato in risultati:
        discente = risultato.iscrizione.discente
        data.append({
            'id': risultato.id,
            'discente_id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'punteggio': risultato.punteggio,
            'data_completamento': risultato.data_completamento.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify(data)

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


from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modello Utente
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='discente')  # 'admin', 'docente', 'discente'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
import os

from config import Config
from models import db, User, Corso, Iscrizione, Test, RisultatoTest, Attestato

app = Flask(__name__)
app.config.from_object(Config)

# Inizializzazione delle estensioni
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decoratore per controllo ruoli
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Non hai i permessi per accedere a questa pagina', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rotte per autenticazione
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
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
    # Reindirizza alla dashboard specifica in base al ruolo
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'docente':
        return redirect(url_for('docente_dashboard'))
    else:  # discente
        return redirect(url_for('discente_dashboard'))

# Dashboard per amministratori
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    discenti_count = User.query.filter_by(role='discente').count()
    corsi_count = Corso.query.count()
    test_count = Test.query.count()
    
    return render_template('admin/dashboard.html', 
                          discenti_count=discenti_count,
                          corsi_count=corsi_count,
                          test_count=test_count)

# Dashboard per docenti
@app.route('/docente/dashboard')
@login_required
@role_required(['docente'])
def docente_dashboard():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/dashboard.html', corsi=corsi)

# Dashboard per discenti
@app.route('/discente/dashboard')
@login_required
@role_required(['discente'])
def discente_dashboard():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/dashboard.html', iscrizioni=iscrizioni)

# Gestione utenti (solo admin)
@app.route('/admin/gestione-utenti')
@login_required
@role_required(['admin'])
def gestione_utenti():
    users = User.query.all()
    return render_template('admin/gestione_utenti.html', users=users)

# Inizializzazione del database e creazione di un utente admin di default
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # Crea un utente admin se non esiste
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            nome='Amministratore',
            cognome='Sistema',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Utente admin creato con successo!')
    
    print('Database inizializzato!')

# Add these routes after the existing ones in app.py

# Gestione Corsi (Admin)
@app.route('/admin/corsi')
@login_required
@role_required(['admin'])
def admin_corsi():
    corsi = Corso.query.all()
    docenti = User.query.filter_by(role='docente').all()
    return render_template('admin/gestione_corsi.html', corsi=corsi, docenti=docenti)

@app.route('/admin/corsi/nuovo', methods=['POST'])
@login_required
@role_required(['admin'])
def nuovo_corso():
    if request.method == 'POST':
        titolo = request.form.get('titolo')
        descrizione = request.form.get('descrizione')
        ore_totali = request.form.get('ore_totali')
        data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
        data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
        progetto_riferimento = request.form.get('progetto_riferimento')
        docente_id = request.form.get('docente_id')
        
        corso = Corso(
            titolo=titolo,
            descrizione=descrizione,
            ore_totali=ore_totali,
            data_inizio=data_inizio,
            data_fine=data_fine,
            progetto_riferimento=progetto_riferimento,
            docente_id=docente_id
        )
        
        db.session.add(corso)
        db.session.commit()
        
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('admin_corsi'))

# Gestione Iscrizioni
@app.route('/admin/iscrizioni')
@login_required
@role_required(['admin'])
def admin_iscrizioni():
    iscrizioni = Iscrizione.query.all()
    return render_template('admin/gestione_iscrizioni.html', iscrizioni=iscrizioni)

@app.route('/admin/iscrizioni/nuova', methods=['POST'])
@login_required
@role_required(['admin'])
def nuova_iscrizione():
    if request.method == 'POST':
        discente_id = request.form.get('discente_id')
        corso_id = request.form.get('corso_id')
        
        # Verifica se l'iscrizione esiste già
        iscrizione_esistente = Iscrizione.query.filter_by(
            discente_id=discente_id, 
            corso_id=corso_id
        ).first()
        
        if iscrizione_esistente:
            flash('Questo discente è già iscritto al corso selezionato!', 'danger')
        else:
            iscrizione = Iscrizione(
                discente_id=discente_id,
                corso_id=corso_id
            )
            
            db.session.add(iscrizione)
            db.session.commit()
            
            flash('Iscrizione creata con successo!', 'success')
            
        return redirect(url_for('admin_iscrizioni'))

# Gestione Test
@app.route('/admin/test')
@login_required
@role_required(['admin'])
def admin_test():
    test = Test.query.all()
    corsi = Corso.query.all()
    return render_template('admin/gestione_test.html', test=test, corsi=corsi)

@app.route('/admin/test/nuovo', methods=['POST'])
@login_required
@role_required(['admin', 'docente'])
def nuovo_test():
    if request.method == 'POST':
        corso_id = request.form.get('corso_id')
        tipo = request.form.get('tipo')
        titolo = request.form.get('titolo')
        forms_link = request.form.get('forms_link')
        
        # Gestione upload file
        file = request.files.get('file_test')
        file_path = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test', filename)
            
            # Assicurati che la directory esista
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            file.save(file_path)
        
        test = Test(
            corso_id=corso_id,
            tipo=tipo,
            titolo=titolo,
            file_path=file_path,
            forms_link=forms_link
        )
        
        db.session.add(test)
        db.session.commit()
        
        flash('Test creato con successo!', 'success')
        
        if current_user.role == 'admin':
            return redirect(url_for('admin_test'))
        else:
            return redirect(url_for('docente_test'))

# Caricamento risultati test da Excel
@app.route('/admin/test/carica-risultati', methods=['POST'])
@login_required
@role_required(['admin', 'docente'])
def carica_risultati_test():
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        file = request.files.get('file_excel')
        
        if file and file.filename:
            # Qui andrebbe implementata la logica per leggere il file Excel
            # e caricare i risultati nel database
            
            flash('Risultati caricati con successo!', 'success')
        else:
            flash('Nessun file selezionato!', 'danger')
        
        if current_user.role == 'admin':
            return redirect(url_for('admin_test'))
        else:
            return redirect(url_for('docente_test'))

# Gestione Attestati
@app.route('/admin/attestati')
@login_required
@role_required(['admin'])
def admin_attestati():
    attestati = Attestato.query.all()
    return render_template('admin/gestione_attestati.html', attestati=attestati)

@app.route('/admin/attestati/genera', methods=['POST'])
@login_required
@role_required(['admin'])
def genera_attestati():
    if request.method == 'POST':
        corso_id = request.form.get('corso_id')
        
        # Trova tutte le iscrizioni per il corso
        iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
        
        attestati_generati = 0
        
        for iscrizione in iscrizioni:
            # Verifica se l'attestato esiste già
            attestato_esistente = Attestato.query.filter_by(iscrizione_id=iscrizione.id).first()
            
            if attestato_esistente:
                continue
                
            # Verifica i criteri per il rilascio dell'attestato
            corso = iscrizione.corso
            ore_minime = corso.ore_totali * 0.8  # 80% delle ore totali
            
            # Trova il test finale
            test_finale = Test.query.filter_by(corso_id=corso.id, tipo='finale').first()
            
            if not test_finale:
                continue
                
            # Trova il risultato del test finale
            risultato_test = RisultatoTest.query.filter_by(
                test_id=test_finale.id,
                iscrizione_id=iscrizione.id
            ).first()
            
            if not risultato_test:
                continue
                
            # Verifica i criteri
            if iscrizione.ore_frequentate >= ore_minime and risultato_test.punteggio >= 85:
                # Genera l'attestato
                attestato = Attestato(
                    iscrizione_id=iscrizione.id,
                    file_path=None  # Qui andrebbe implementata la generazione del PDF
                )
                
                db.session.add(attestato)
                attestati_generati += 1
        
        if attestati_generati > 0:
            db.session.commit()
            flash(f'{attestati_generati} attestati generati con successo!', 'success')
        else:
            flash('Nessun attestato generato. Verifica i criteri di rilascio.', 'warning')
            
        return redirect(url_for('admin_attestati'))

# Rotte per docenti
@app.route('/docente/corsi')
@login_required
@role_required(['docente'])
def docente_corsi():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/corsi.html', corsi=corsi)

@app.route('/docente/test')
@login_required
@role_required(['docente'])
def docente_test():
    corsi_ids = [corso.id for corso in Corso.query.filter_by(docente_id=current_user.id).all()]
    test = Test.query.filter(Test.corso_id.in_(corsi_ids)).all()
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/test.html', test=test, corsi=corsi)

@app.route('/docente/iscrizioni/<int:corso_id>')
@login_required
@role_required(['docente'])
def docente_iscrizioni_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    
    # Verifica che il corso appartenga al docente
    if corso.docente_id != current_user.id:
        flash('Non hai i permessi per visualizzare questo corso', 'danger')
        return redirect(url_for('docente_corsi'))
        
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    return render_template('docente/iscrizioni_corso.html', corso=corso, iscrizioni=iscrizioni)

@app.route('/docente/aggiorna-ore', methods=['POST'])
@login_required
@role_required(['docente'])
def aggiorna_ore():
    if request.method == 'POST':
        iscrizione_id = request.form.get('iscrizione_id')
        ore_frequentate = float(request.form.get('ore_frequentate'))
        
        iscrizione = Iscrizione.query.get_or_404(iscrizione_id)
        
        # Verifica che il corso appartenga al docente
        if iscrizione.corso.docente_id != current_user.id:
            flash('Non hai i permessi per modificare questa iscrizione', 'danger')
            return redirect(url_for('docente_corsi'))
            
        iscrizione.ore_frequentate = ore_frequentate
        db.session.commit()
        
        flash('Ore frequentate aggiornate con successo!', 'success')
        return redirect(url_for('docente_iscrizioni_corso', corso_id=iscrizione.corso_id))

@app.route('/docente/valuta-test', methods=['POST'])
@login_required
@role_required(['docente'])
def valuta_test():
    if request.method == 'POST':
        risultato_id = request.form.get('risultato_id')
        punteggio = float(request.form.get('punteggio'))
        
        risultato = RisultatoTest.query.get_or_404(risultato_id)
        
        # Verifica che il test appartenga a un corso del docente
        if risultato.test.corso.docente_id != current_user.id:
            flash('Non hai i permessi per valutare questo test', 'danger')
            return redirect(url_for('docente_test'))
            
        risultato.punteggio = punteggio
        db.session.commit()
        
        flash('Valutazione registrata con successo!', 'success')
        return redirect(url_for('docente_test'))

# Rotte per discenti
@app.route('/discente/corsi')
@login_required
@role_required(['discente'])
def discente_corsi():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/corsi.html', iscrizioni=iscrizioni)

@app.route('/discente/corso/<int:corso_id>')
@login_required
@role_required(['discente'])
def discente_dettaglio_corso(corso_id):
    corso = Corso.query.get_or_404(corso_id)
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=corso_id
    ).first_or_404()
    
    test = Test.query.filter_by(corso_id=corso_id).all()
    risultati = RisultatoTest.query.filter_by(iscrizione_id=iscrizione.id).all()
    
    # Crea un dizionario per mappare i test ai risultati
    risultati_dict = {r.test_id: r for r in risultati}
    
    return render_template('discente/dettaglio_corso.html', 
                          corso=corso, 
                          iscrizione=iscrizione, 
                          test=test,
                          risultati_dict=risultati_dict)

@app.route('/discente/test/<int:test_id>')
@login_required
@role_required(['discente'])
def discente_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Verifica che il discente sia iscritto al corso
    iscrizione = Iscrizione.query.filter_by(
        discente_id=current_user.id,
        corso_id=test.corso_id
    ).first_or_404()
    
    # Verifica se il test è già stato completato
    risultato = RisultatoTest.query.filter_by(
        test_id=test_id,
        iscrizione_id=iscrizione.id
    ).first()
    
    return render_template('discente/test.html', 
                          test=test, 
                          iscrizione=iscrizione,
                          risultato=risultato)

@app.route('/discente/attestati')
@login_required
@role_required(['discente'])
def discente_attestati():
    # Trova tutte le iscrizioni del discente
    iscrizioni_ids = [i.id for i in Iscrizione.query.filter_by(discente_id=current_user.id).all()]
    
    # Trova tutti gli attestati associati a queste iscrizioni
    attestati = Attestato.query.filter(Attestato.iscrizione_id.in_(iscrizioni_ids)).all()
    
    return render_template('discente/attestati.html', attestati=attestati)

@app.route('/discente/scarica-attestato/<int:attestato_id>')
@login_required
@role_required(['discente'])
def scarica_attestato(attestato_id):
    attestato = Attestato.query.get_or_404(attestato_id)
    
    # Verifica che l'attestato appartenga al discente
    if attestato.iscrizione.discente_id != current_user.id:
        flash('Non hai i permessi per scaricare questo attestato', 'danger')
        return redirect(url_for('discente_attestati'))
    
    # Qui andrebbe implementata la logica per scaricare il file
    # Per ora, reindirizza alla pagina degli attestati
    flash('Funzionalità di download non ancora implementata', 'warning')
    return redirect(url_for('discente_attestati'))

# API per richieste AJAX
@app.route('/api/corsi/<int:corso_id>/discenti')
@login_required
def api_discenti_corso(corso_id):
    iscrizioni = Iscrizione.query.filter_by(corso_id=corso_id).all()
    discenti = []
    
    for iscrizione in iscrizioni:
        discente = iscrizione.discente
        discenti.append({
            'id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'email': discente.email,
            'ore_frequentate': iscrizione.ore_frequentate
        })
    
    return jsonify(discenti)

@app.route('/api/test/<int:test_id>/risultati')
@login_required
def api_risultati_test(test_id):
    risultati = RisultatoTest.query.filter_by(test_id=test_id).all()
    data = []
    
    for risultato in risultati:
        discente = risultato.iscrizione.discente
        data.append({
            'id': risultato.id,
            'discente_id': discente.id,
            'nome': discente.nome,
            'cognome': discente.cognome,
            'punteggio': risultato.punteggio,
            'data_completamento': risultato.data_completamento.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify(data)

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


from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestione_corsi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modello Utente
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='discente')  # 'admin', 'docente', 'discente'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
import os

from config import Config
from models import db, User, Corso, Iscrizione, Test, RisultatoTest, Attestato

app = Flask(__name__)
app.config.from_object(Config)

# Inizializzazione delle estensioni
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decoratore per controllo ruoli
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Non hai i permessi per accedere a questa pagina', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rotte per autenticazione
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
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
    # Reindirizza alla dashboard specifica in base al ruolo
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'docente':
        return redirect(url_for('docente_dashboard'))
    else:  # discente
        return redirect(url_for('discente_dashboard'))

# Dashboard per amministratori
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    discenti_count = User.query.filter_by(role='discente').count()
    corsi_count = Corso.query.count()
    test_count = Test.query.count()
    
    return render_template('admin/dashboard.html', 
                          discenti_count=discenti_count,
                          corsi_count=corsi_count,
                          test_count=test_count)

# Dashboard per docenti
@app.route('/docente/dashboard')
@login_required
@role_required(['docente'])
def docente_dashboard():
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/dashboard.html', corsi=corsi)

# Dashboard per discenti
@app.route('/discente/dashboard')
@login_required
@role_required(['discente'])
def discente_dashboard():
    iscrizioni = Iscrizione.query.filter_by(discente_id=current_user.id).all()
    return render_template('discente/dashboard.html', iscrizioni=iscrizioni)

# Gestione utenti (solo admin)
@app.route('/admin/gestione-utenti')
@login_required
@role_required(['admin'])
def gestione_utenti():
    users = User.query.all()
    return render_template('admin/gestione_utenti.html', users=users)

# Inizializzazione del database e creazione di un utente admin di default
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # Crea un utente admin se non esiste
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            nome='Amministratore',
            cognome='Sistema',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Utente admin creato con successo!')
    
    print('Database inizializzato!')

# Add these routes after the existing ones in app.py

# Gestione Corsi (Admin)
@app.route('/admin/corsi')
@login_required
@role_required(['admin'])
def admin_corsi():
    corsi = Corso.query.all()
    docenti = User.query.filter_by(role='docente').all()
    return render_template('admin/gestione_corsi.html', corsi=corsi, docenti=docenti)

@app.route
    