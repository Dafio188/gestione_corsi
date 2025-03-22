from flask import render_template, redirect, url_for, flash, request, abort
from datetime import datetime
from werkzeug.utils import secure_filename
import os

# These will be imported when this module is imported in run.py
# after the app and other objects are created
app = None
db = None
role_required = None
Progetto = None
Corso = None
User = None

def init_routes(flask_app, database, role_req, models):
    """Initialize routes with application context"""
    global app, db, role_required, Progetto, Corso, User
    app = flask_app
    db = database
    role_required = role_req
    Progetto = models['Progetto']
    Corso = models['Corso']
    User = models['User']
    
    # Now register all the routes
    register_routes()

def register_routes():
    """Register all project-related routes"""
    
    @app.route('/admin/gestione-progetti')
    @role_required('admin')
    def admin_gestione_progetti():
        progetti = Progetto.query.all()
        return render_template('admin/progetti.html', progetti=progetti)

    @app.route('/admin/progetti/crea', methods=['GET', 'POST'])
    @role_required('admin')
    def admin_crea_progetto():
        if request.method == 'POST':
            titolo = request.form.get('titolo')
            descrizione = request.form.get('descrizione')
            data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
            data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
            budget = float(request.form.get('budget') or 0)
            
            progetto = Progetto(
                titolo=titolo,
                descrizione=descrizione,
                data_inizio=data_inizio,
                data_fine=data_fine,
                budget=budget
            )
            
            db.session.add(progetto)
            db.session.commit()
            
            flash('Progetto creato con successo', 'success')
            return redirect(url_for('admin_gestione_progetti'))  # Changed from 'admin_progetti'
        
        return render_template('admin/nuovo_progetto.html')

    @app.route('/admin/progetti/<int:progetto_id>')
    @role_required(['admin'])
    def admin_dettaglio_progetto(progetto_id):
        progetto = db.session.get(Progetto, progetto_id)
        if not progetto:
            abort(404)
        
        # Get courses and students associated with this project
        corsi = Corso.query.filter_by(progetto_id=progetto_id).all()
        discenti = User.query.filter_by(progetto_id=progetto_id, role='discente').all()
        
        return render_template('admin/dettaglio_progetto.html', 
                            progetto=progetto,
                            corsi=corsi,
                            discenti=discenti)

    @app.route('/admin/progetti/<int:progetto_id>/modifica', methods=['GET', 'POST'])
    @role_required(['admin'])
    def admin_modifica_progetto(progetto_id):
        progetto = db.session.get(Progetto, progetto_id)
        if not progetto:
            abort(404)
        
        if request.method == 'POST':
            # Update project information
            progetto.titolo = request.form.get('titolo')
            progetto.descrizione = request.form.get('descrizione')
            progetto.data_inizio = datetime.strptime(request.form.get('data_inizio'), '%Y-%m-%d')
            progetto.data_fine = datetime.strptime(request.form.get('data_fine'), '%Y-%m-%d')
            progetto.budget = float(request.form.get('budget') or 0)
            
            db.session.commit()
            flash('Progetto aggiornato con successo', 'success')
            return redirect(url_for('admin_gestione_progetti'))  # Changed from 'admin_progetti'
        
        return render_template('admin/modifica_progetto.html', progetto=progetto)

    @app.route('/admin/progetti/<int:progetto_id>/elimina', methods=['POST'])
    @role_required(['admin'])
    def admin_elimina_progetto(progetto_id):
        progetto = db.session.get(Progetto, progetto_id)
        if not progetto:
            abort(404)
        
        # Check if there are any courses associated with this project
        corsi = Corso.query.filter_by(progetto_id=progetto_id).all()
        
        # Update courses to remove project association
        for corso in corsi:
            corso.progetto_id = None
            corso.progetto_riferimento = f"Ex-{progetto.titolo} (Eliminato)"
        
        # Update users to remove project association
        discenti = User.query.filter_by(progetto_id=progetto_id).all()
        for discente in discenti:
            discente.progetto_id = None
        
        # Delete the project
        db.session.delete(progetto)
        db.session.commit()
        
        flash('Progetto eliminato con successo', 'success')
        # Make sure all redirects use admin_gestione_progetti instead of admin_progetti
        return redirect(url_for('admin_gestione_progetti'))

# Add this at the top of your file if it's not already there
from flask import Blueprint

# Create a blueprint
bp = Blueprint('progetti', __name__)

# Change your route decorators from @app.route to @bp.route
@bp.route('/admin/progetti')
def admin_progetti():
    pass