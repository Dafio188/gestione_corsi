from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import DisponibilitaDocente, User, Corso
from extensions import db
from datetime import datetime
from functools import wraps

calendario_bp = Blueprint('calendario', __name__)

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.ruolo not in roles:
                return jsonify({'error': 'Non autorizzato'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@calendario_bp.route('/admin/calendario')
@login_required
@role_required(['admin'])
def admin_calendario():
    """Vista principale del calendario admin"""
    docenti = User.query.filter_by(ruolo='docente').all()
    corsi = Corso.query.all()
    return render_template('admin/calendario_completo.html', docenti=docenti, corsi=corsi)

@calendario_bp.route('/docente/calendario')
@login_required
@role_required(['docente'])
def docente_calendario():
    """Vista principale del calendario docente"""
    return render_template('docente/calendario_completo.html')

@calendario_bp.route('/admin/calendario/eventi')
@login_required
@role_required(['admin'])
def admin_calendario_eventi():
    """API per ottenere gli eventi del calendario admin"""
    start = request.args.get('start')
    end = request.args.get('end')
    docente_id = request.args.get('docente_id', 'all')
    corso_id = request.args.get('corso_id', 'all')
    stato = request.args.get('stato', 'all')
    
    print(f"Richiesta eventi: start={start}, end={end}, docente_id={docente_id}, corso_id={corso_id}, stato={stato}")
    
    query = DisponibilitaDocente.query
    
    if start:
        try:
            start_date = datetime.fromisoformat(start[:10]).date()
            query = query.filter(DisponibilitaDocente.data >= start_date)
            print(f"Filtro data inizio: {start_date}")
        except Exception as e:
            print(f"Errore nel parsing della data di inizio: {e}")
    
    if end:
        try:
            end_date = datetime.fromisoformat(end[:10]).date()
            query = query.filter(DisponibilitaDocente.data <= end_date)
            print(f"Filtro data fine: {end_date}")
        except Exception as e:
            print(f"Errore nel parsing della data di fine: {e}")
    
    if docente_id != 'all':
        try:
            docente_id_int = int(docente_id)
            query = query.filter(DisponibilitaDocente.docente_id == docente_id_int)
            print(f"Filtro docente: {docente_id_int}")
        except Exception as e:
            print(f"Errore nel parsing del docente_id: {e}")
    
    if corso_id != 'all':
        try:
            corso_id_int = int(corso_id)
            query = query.filter(DisponibilitaDocente.corso_id == corso_id_int)
            print(f"Filtro corso: {corso_id_int}")
        except Exception as e:
            print(f"Errore nel parsing del corso_id: {e}")
    
    if stato != 'all':
        query = query.filter(DisponibilitaDocente.stato == stato)
        print(f"Filtro stato: {stato}")
    
    try:
        disponibilita = query.all()
        print(f"Eventi trovati: {len(disponibilita)}")
        
        result = [d.to_dict() for d in disponibilita]
        print(f"Eventi serializzati: {result}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Errore nella query: {e}")
        return jsonify([])

@calendario_bp.route('/docente/calendario/eventi')
@login_required
@role_required(['docente'])
def docente_calendario_eventi():
    """API per ottenere gli eventi del calendario docente"""
    start = request.args.get('start')
    end = request.args.get('end')
    stato = request.args.get('stato', 'all')
    
    query = DisponibilitaDocente.query.filter_by(docente_id=current_user.id)
    
    if start:
        query = query.filter(DisponibilitaDocente.data >= datetime.fromisoformat(start[:10]).date())
    if end:
        query = query.filter(DisponibilitaDocente.data <= datetime.fromisoformat(end[:10]).date())
    if stato != 'all':
        query = query.filter(DisponibilitaDocente.stato == stato)
        
    disponibilita = query.all()
    return jsonify([d.to_dict() for d in disponibilita])

@calendario_bp.route('/api/calendario/eventi', methods=['POST'])
@login_required
def create_event():
    """API per creare un nuovo evento"""
    data = request.get_json()
    
    # Validazione base
    required_fields = ['start', 'end', 'docente_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Campi obbligatori mancanti'}), 400
        
    # Converti le date
    try:
        start_datetime = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Formato data non valido'}), 400
        
    # Crea disponibilità
    disponibilita = DisponibilitaDocente(
        docente_id=data['docente_id'],
        data=start_datetime.date(),
        ora_inizio=start_datetime.time(),
        ora_fine=end_datetime.time(),
        corso_id=data.get('corso_id'),
        note=data.get('note', ''),
        stato=data.get('stato', 'disponibile')
    )
    
    db.session.add(disponibilita)
    try:
        db.session.commit()
        return jsonify(disponibilita.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@calendario_bp.route('/api/calendario/eventi/<int:id>', methods=['PUT'])
@login_required
def update_event(id):
    """API per aggiornare un evento esistente"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    data = request.get_json()
    
    # Verifica permessi
    if current_user.ruolo != 'admin' and disponibilita.docente_id != current_user.id:
        return jsonify({'error': 'Non autorizzato'}), 403
        
    # Aggiorna i campi
    if 'start' in data:
        start_datetime = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        disponibilita.data = start_datetime.date()
        disponibilita.ora_inizio = start_datetime.time()
    if 'end' in data:
        end_datetime = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
        disponibilita.ora_fine = end_datetime.time()
    if 'stato' in data:
        disponibilita.stato = data['stato']
    if 'note' in data:
        disponibilita.note = data['note']
    if 'corso_id' in data:
        disponibilita.corso_id = data['corso_id']
        
    db.session.commit()
    return jsonify(disponibilita.to_dict())

@calendario_bp.route('/api/calendario/eventi/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def update_event_form(id):
    """API per aggiornare un evento esistente tramite form POST"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    
    # Aggiorna i campi
    if 'data' in request.form:
        disponibilita.data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
    if 'ora_inizio' in request.form:
        disponibilita.ora_inizio = datetime.strptime(request.form['ora_inizio'], '%H:%M').time()
    if 'ora_fine' in request.form:
        disponibilita.ora_fine = datetime.strptime(request.form['ora_fine'], '%H:%M').time()
    if 'stato' in request.form:
        disponibilita.stato = request.form['stato']
    if 'note' in request.form:
        disponibilita.note = request.form['note']
    if 'libera' in request.form and request.form['libera'] == 'on':
        disponibilita.stato = 'disponibile'
        disponibilita.corso_id = None
        
    db.session.commit()
    flash('Disponibilità aggiornata con successo!', 'success')
    return redirect(url_for('disponibilita.admin_disponibilita'))

@calendario_bp.route('/api/calendario/eventi/<int:id>', methods=['DELETE'])
@login_required
def delete_event(id):
    """API per eliminare un evento"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    
    # Verifica permessi - gli admin possono eliminare qualsiasi evento
    if current_user.ruolo != 'admin' and disponibilita.docente_id != current_user.id:
        return jsonify({'error': 'Non autorizzato'}), 403
        
    db.session.delete(disponibilita)
    db.session.commit()
    return '', 204 