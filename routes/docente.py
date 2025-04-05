from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Corso, DisponibilitaDocente, Note
from extensions import db
from functools import wraps

docente_bp = Blueprint('docente', __name__)

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.ruolo not in roles:
                return jsonify({'error': 'Non autorizzato'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@docente_bp.route('/dashboard')
@login_required
@role_required(['docente'])
def docente_dashboard():
    """Vista principale della dashboard docente"""
    # Recupera i contatori
    corsi_count = Corso.query.filter_by(docente_id=current_user.id).count()
    disponibilita_count = DisponibilitaDocente.query.filter_by(docente_id=current_user.id).count()
    note_count = Note.query.filter_by(docente_id=current_user.id).count() if hasattr(Note, 'docente_id') else 0
    
    # Recupera i corsi per la lista
    corsi = Corso.query.filter_by(docente_id=current_user.id).all()
    
    return render_template('docente/dashboard.html',
                         corsi_count=corsi_count,
                         disponibilita_count=disponibilita_count,
                         note_count=note_count,
                         corsi=corsi) 