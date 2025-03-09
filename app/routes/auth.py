from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models.models import db, Discente, Progetto  # Importa Progetto
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ✅ PAGINA DI LOGIN
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Cerca l'utente nel database
        user = Discente.query.filter_by(email=email).first()

        if user and user.check_password(password):  # Assicurati che check_password esista nel modello
            login_user(user)
            flash('Login effettuato con successo!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Email o password errate.', 'danger')

    return render_template('auth/login.html')

# ✅ LOGOUT
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo.', 'info')
    return redirect(url_for('auth.login'))

# ✅ PAGINA DI REGISTRAZIONE
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    progetti = Progetto.query.all()  # Recupera tutti i progetti disponibili

    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        codice_fiscale = request.form.get('codice_fiscale')
        email = request.form.get('email')
        password = request.form.get('password')
        progetto_id = request.form.get('progetto_id')

        # Controlla se l'utente esiste già
        existing_user = Discente.query.filter_by(email=email).first()
        if existing_user:
            flash('Esiste già un account con questa email.', 'danger')
            return redirect(url_for('auth.register'))

        # Controlla se il progetto è valido
        if not progetto_id or not progetto_id.isdigit():
            flash('Seleziona un progetto valido.', 'danger')
            return redirect(url_for('auth.register'))

        # Assicura che il progetto esista nel database
        progetto = Progetto.query.get(int(progetto_id))
        if not progetto:
            flash('Progetto selezionato non valido.', 'danger')
            return redirect(url_for('auth.register'))

        try:
            # Crea un nuovo utente
            new_user = Discente(
                nome=nome,
                cognome=cognome,
                codice_fiscale=codice_fiscale,
                email=email,
                password_hash=generate_password_hash(password),
                progetto_id=int(progetto_id)  # Assicura che il valore sia un intero
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Registrazione completata! Ora puoi accedere.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()  # Annulla l'operazione se c'è un errore
            flash(f'Errore durante la registrazione: {str(e)}', 'danger')

    return render_template('auth/register.html', progetti=progetti)
