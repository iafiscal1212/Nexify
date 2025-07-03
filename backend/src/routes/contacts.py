from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.contact import Contact, SocialProfile, Connection
from src.models.analytics import ActivityLog
from datetime import datetime

contacts_bp = Blueprint('contacts', __name__)

# CRUD para Contactos
@contacts_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Obtener todos los contactos del usuario"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = Contact.query.filter_by(user_id=user_id)
    
    if search:
        query = query.filter(
            db.or_(
                Contact.name.contains(search),
                Contact.company.contains(search),
                Contact.position.contains(search),
                Contact.industry.contains(search)
            )
        )
    
    contacts = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'contacts': [contact.to_dict() for contact in contacts.items],
        'total': contacts.total,
        'pages': contacts.pages,
        'current_page': page
    })

@contacts_bp.route('/contacts', methods=['POST'])
def create_contact():
    """Crear un nuevo contacto"""
    data = request.json
    
    required_fields = ['user_id', 'name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    contact = Contact(
        user_id=data['user_id'],
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        company=data.get('company'),
        position=data.get('position'),
        industry=data.get('industry'),
        location=data.get('location'),
        notes=data.get('notes')
    )
    
    db.session.add(contact)
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=data['user_id'],
        action='contact_added',
        entity_type='contact',
        entity_id=contact.id,
        details={'contact_name': contact.name}
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify(contact.to_dict()), 201

@contacts_bp.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Obtener un contacto específico"""
    contact = Contact.query.get_or_404(contact_id)
    return jsonify(contact.to_dict())

@contacts_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Actualizar un contacto"""
    contact = Contact.query.get_or_404(contact_id)
    data = request.json
    
    # Actualizar campos
    for field in ['name', 'email', 'phone', 'company', 'position', 'industry', 'location', 'notes']:
        if field in data:
            setattr(contact, field, data[field])
    
    contact.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=contact.user_id,
        action='contact_updated',
        entity_type='contact',
        entity_id=contact.id,
        details={'contact_name': contact.name}
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify(contact.to_dict())

@contacts_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Eliminar un contacto"""
    contact = Contact.query.get_or_404(contact_id)
    user_id = contact.user_id
    contact_name = contact.name
    
    db.session.delete(contact)
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=user_id,
        action='contact_deleted',
        entity_type='contact',
        entity_id=contact_id,
        details={'contact_name': contact_name}
    )
    db.session.add(log)
    db.session.commit()
    
    return '', 204

# CRUD para Perfiles Sociales
@contacts_bp.route('/contacts/<int:contact_id>/social-profiles', methods=['GET'])
def get_social_profiles(contact_id):
    """Obtener perfiles sociales de un contacto"""
    contact = Contact.query.get_or_404(contact_id)
    return jsonify([profile.to_dict() for profile in contact.social_profiles])

@contacts_bp.route('/contacts/<int:contact_id>/social-profiles', methods=['POST'])
def create_social_profile(contact_id):
    """Agregar perfil social a un contacto"""
    contact = Contact.query.get_or_404(contact_id)
    data = request.json
    
    required_fields = ['platform', 'username']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Verificar que la plataforma sea válida
    valid_platforms = ['tiktok', 'instagram', 'facebook', 'linkedin']
    if data['platform'] not in valid_platforms:
        return jsonify({'error': f'platform must be one of: {", ".join(valid_platforms)}'}), 400
    
    profile = SocialProfile(
        contact_id=contact_id,
        platform=data['platform'],
        username=data['username'],
        profile_url=data.get('profile_url'),
        followers_count=data.get('followers_count'),
        following_count=data.get('following_count'),
        posts_count=data.get('posts_count'),
        engagement_rate=data.get('engagement_rate'),
        verified=data.get('verified', False),
        bio=data.get('bio')
    )
    
    db.session.add(profile)
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=contact.user_id,
        action='social_profile_added',
        entity_type='social_profile',
        entity_id=profile.id,
        details={
            'contact_name': contact.name,
            'platform': profile.platform,
            'username': profile.username
        }
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify(profile.to_dict()), 201

@contacts_bp.route('/social-profiles/<int:profile_id>', methods=['PUT'])
def update_social_profile(profile_id):
    """Actualizar perfil social"""
    profile = SocialProfile.query.get_or_404(profile_id)
    data = request.json
    
    # Actualizar campos
    for field in ['username', 'profile_url', 'followers_count', 'following_count', 
                  'posts_count', 'engagement_rate', 'verified', 'bio']:
        if field in data:
            setattr(profile, field, data[field])
    
    profile.last_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify(profile.to_dict())

@contacts_bp.route('/social-profiles/<int:profile_id>', methods=['DELETE'])
def delete_social_profile(profile_id):
    """Eliminar perfil social"""
    profile = SocialProfile.query.get_or_404(profile_id)
    contact = profile.contact
    
    db.session.delete(profile)
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=contact.user_id,
        action='social_profile_deleted',
        entity_type='social_profile',
        entity_id=profile_id,
        details={
            'contact_name': contact.name,
            'platform': profile.platform,
            'username': profile.username
        }
    )
    db.session.add(log)
    db.session.commit()
    
    return '', 204

# Endpoints para búsqueda y filtrado
@contacts_bp.route('/contacts/search', methods=['GET'])
def search_contacts():
    """Búsqueda avanzada de contactos"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Parámetros de búsqueda
    name = request.args.get('name', '')
    company = request.args.get('company', '')
    industry = request.args.get('industry', '')
    location = request.args.get('location', '')
    platform = request.args.get('platform', '')
    
    query = Contact.query.filter_by(user_id=user_id)
    
    if name:
        query = query.filter(Contact.name.contains(name))
    if company:
        query = query.filter(Contact.company.contains(company))
    if industry:
        query = query.filter(Contact.industry.contains(industry))
    if location:
        query = query.filter(Contact.location.contains(location))
    
    if platform:
        query = query.join(SocialProfile).filter(SocialProfile.platform == platform)
    
    contacts = query.all()
    return jsonify([contact.to_dict() for contact in contacts])

@contacts_bp.route('/contacts/stats', methods=['GET'])
def get_contacts_stats():
    """Obtener estadísticas de contactos"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    total_contacts = Contact.query.filter_by(user_id=user_id).count()
    
    # Estadísticas por industria
    industry_stats = db.session.query(
        Contact.industry, 
        db.func.count(Contact.id).label('count')
    ).filter_by(user_id=user_id).filter(
        Contact.industry.isnot(None)
    ).group_by(Contact.industry).all()
    
    # Estadísticas por ubicación
    location_stats = db.session.query(
        Contact.location, 
        db.func.count(Contact.id).label('count')
    ).filter_by(user_id=user_id).filter(
        Contact.location.isnot(None)
    ).group_by(Contact.location).all()
    
    # Estadísticas por plataforma social
    platform_stats = db.session.query(
        SocialProfile.platform,
        db.func.count(SocialProfile.id).label('count')
    ).join(Contact).filter(
        Contact.user_id == user_id
    ).group_by(SocialProfile.platform).all()
    
    return jsonify({
        'total_contacts': total_contacts,
        'by_industry': [{'industry': stat[0], 'count': stat[1]} for stat in industry_stats],
        'by_location': [{'location': stat[0], 'count': stat[1]} for stat in location_stats],
        'by_platform': [{'platform': stat[0], 'count': stat[1]} for stat in platform_stats]
    })

