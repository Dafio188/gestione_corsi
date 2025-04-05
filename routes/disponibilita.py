from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import DisponibilitaDocente, User, Corso
from extensions import db
from datetime import datetime
from functools import wraps
from forms import DisponibilitaForm

disponibilita_bp = Blueprint('disponibilita', __name__)

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.ruolo not in roles:
                return jsonify({'error': 'Non autorizzato'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@disponibilita_bp.route('/admin/disponibilita')
@login_required
@role_required(['admin'])
def admin_disponibilita():
    """Vista principale della disponibilità per l'admin"""
    docenti = User.query.filter_by(ruolo='docente').all()
    corsi = Corso.query.all()
    
    # Recupera il filtro per docente
    docente_id = request.args.get('docente_id', type=int)
    
    # Query base
    query = DisponibilitaDocente.query
    
    # Applica il filtro per docente se presente
    if docente_id:
        query = query.filter_by(docente_id=docente_id)
    
    # Ordina per data e ora_inizio
    disponibilita = query.order_by(DisponibilitaDocente.data.desc(), DisponibilitaDocente.ora_inizio).all()
    
    return render_template('admin/disponibilita.html', docenti=docenti, corsi=corsi, disponibilita=disponibilita)

@disponibilita_bp.route('/docente/disponibilita')
@login_required
@role_required(['docente'])
def docente_disponibilita():
    """Vista principale della disponibilità per il docente"""
    disponibilita = DisponibilitaDocente.query.filter_by(docente_id=current_user.id).all()
    return render_template('docente/disponibilita.html', disponibilita=disponibilita)

@disponibilita_bp.route('/admin/disponibilita/eventi')
@login_required
@role_required(['admin'])
def admin_disponibilita_eventi():
    """API per ottenere gli eventi di disponibilità per l'admin"""
    start = request.args.get('start')
    end = request.args.get('end')
    docente_id = request.args.get('docente_id', 'all')
    stato = request.args.get('stato', 'all')
    
    query = DisponibilitaDocente.query
    
    if start:
        query = query.filter(DisponibilitaDocente.data >= datetime.fromisoformat(start[:10]).date())
    if end:
        query = query.filter(DisponibilitaDocente.data <= datetime.fromisoformat(end[:10]).date())
    if docente_id != 'all':
        query = query.filter(DisponibilitaDocente.docente_id == docente_id)
    if stato != 'all':
        query = query.filter(DisponibilitaDocente.stato == stato)
        
    disponibilita = query.all()
    return jsonify([d.to_dict() for d in disponibilita])

@disponibilita_bp.route('/docente/disponibilita/eventi')
@login_required
@role_required(['docente'])
def docente_disponibilita_eventi():
    """API per ottenere gli eventi di disponibilità per il docente"""
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

@disponibilita_bp.route('/api/disponibilita/eventi', methods=['POST'])
@login_required
def create_disponibilita():
    """API per creare una nuova disponibilità"""
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
        
    # Verifica disponibilità
    if not DisponibilitaDocente.is_available(start_datetime, end_datetime, data['docente_id']):
        return jsonify({'error': 'Orario non disponibile'}), 409
        
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
    db.session.commit()
    
    return jsonify(disponibilita.to_dict()), 201

@disponibilita_bp.route('/api/disponibilita/eventi/<int:id>', methods=['PUT'])
@login_required
def update_disponibilita(id):
    """API per aggiornare una disponibilità esistente"""
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

@disponibilita_bp.route('/api/disponibilita/eventi/<int:id>', methods=['DELETE'])
@login_required
def delete_disponibilita(id):
    """API per eliminare una disponibilità"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    
    # Verifica permessi
    if current_user.ruolo != 'admin' and disponibilita.docente_id != current_user.id:
        return jsonify({'error': 'Non autorizzato'}), 403
        
    db.session.delete(disponibilita)
    db.session.commit()
    return '', 204

@disponibilita_bp.route('/docente/nuova_disponibilita', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_nuova_disponibilita():
    """Vista per aggiungere una nuova disponibilità"""
    form = DisponibilitaForm()
    if form.validate_on_submit():
        disponibilita = DisponibilitaDocente(
            docente_id=current_user.id,
            data=form.data.data,
            ora_inizio=form.ora_inizio.data,
            ora_fine=form.ora_fine.data,
            stato=form.stato.data,
            note=form.note.data
        )
        db.session.add(disponibilita)
        db.session.commit()
        flash('Disponibilità aggiunta con successo!', 'success')
        return redirect(url_for('disponibilita.docente_disponibilita'))
    return render_template('docente/nuova_disponibilita.html', form=form)

@disponibilita_bp.route('/docente/modifica_disponibilita/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['docente'])
def docente_modifica_disponibilita(id):
    """Vista per modificare una disponibilità esistente"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    
    # Verifica che la disponibilità appartenga al docente corrente
    if disponibilita.docente_id != current_user.id:
        flash('Non hai i permessi per modificare questa disponibilità.', 'danger')
        return redirect(url_for('disponibilita.docente_disponibilita'))
    
    form = DisponibilitaForm(obj=disponibilita)
    if form.validate_on_submit():
        disponibilita.data = form.data.data
        disponibilita.ora_inizio = form.ora_inizio.data
        disponibilita.ora_fine = form.ora_fine.data
        disponibilita.note = form.note.data
        db.session.commit()
        flash('Disponibilità modificata con successo!', 'success')
        return redirect(url_for('disponibilita.docente_disponibilita'))
    
    return render_template('docente/modifica_disponibilita.html', form=form, disponibilita=disponibilita)

@disponibilita_bp.route('/docente/elimina_disponibilita/<int:id>', methods=['POST'])
@login_required
@role_required(['docente'])
def docente_elimina_disponibilita(id):
    """Vista per eliminare una disponibilità"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    
    # Verifica che la disponibilità appartenga al docente corrente
    if disponibilita.docente_id != current_user.id:
        flash('Non hai i permessi per eliminare questa disponibilità.', 'danger')
        return redirect(url_for('disponibilita.docente_disponibilita'))
    
    db.session.delete(disponibilita)
    db.session.commit()
    flash('Disponibilità eliminata con successo!', 'success')
    return redirect(url_for('disponibilita.docente_disponibilita'))

@disponibilita_bp.route('/admin/prenota_disponibilita/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_prenota_disponibilita(id):
    """Vista per prenotare una disponibilità"""
    disponibilita = DisponibilitaDocente.query.get_or_404(id)
    corso_id = request.form.get('corso_id')
    
    if not corso_id:
        flash('Seleziona un corso per prenotare la disponibilità.', 'danger')
        return redirect(url_for('disponibilita.admin_disponibilita'))
    
    corso = Corso.query.get_or_404(corso_id)
    
    # Verifica che la disponibilità sia disponibile
    if disponibilita.stato != 'disponibile':
        flash('Questa disponibilità non è più disponibile.', 'danger')
        return redirect(url_for('disponibilita.admin_disponibilita'))
    
    # Aggiorna la disponibilità
    disponibilita.stato = 'occupato'
    disponibilita.corso_id = corso_id
    db.session.commit()
    
    flash('Disponibilità prenotata con successo!', 'success')
    return redirect(url_for('disponibilita.admin_disponibilita')) 