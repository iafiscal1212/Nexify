"""
Rutas de autenticación seguras para NEXIFY
Incluye registro, login, logout y gestión de sesiones
"""

from flask import Blueprint, jsonify, request
from src.models.user import db, User
from src.models.analytics import ActivityLog
from src.utils.auth import auth_manager, require_auth, validate_input
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
@validate_input({
    'required': ['username', 'email', 'password'],
    'types': {'username': str, 'email': str, 'password': str}
})
def register():
    """Registrar nuevo usuario con validaciones de seguridad"""
    data = request.validated_data
    
    # Verificar rate limiting
    client_ip = request.remote_addr
    rate_check = auth_manager.rate_limit_check(f"register_{client_ip}", max_attempts=3, window_minutes=60)
    
    if not rate_check['allowed']:
        return jsonify({
            'error': 'Too many registration attempts. Please try again later.',
            'reset_time': rate_check['reset_time'].isoformat()
        }), 429
    
    # Registrar intento
    auth_manager.record_attempt(f"register_{client_ip}")
    
    # Validar email
    if not auth_manager.validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validar fortaleza de contraseña
    password_validation = auth_manager.validate_password_strength(data['password'])
    if not password_validation['valid']:
        return jsonify({
            'error': 'Password does not meet security requirements',
            'details': password_validation['errors']
        }), 400
    
    # Validar username
    if len(data['username']) < 3 or len(data['username']) > 50:
        return jsonify({'error': 'Username must be between 3 and 50 characters'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_]+$', data['username']):
        return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400
    
    # Verificar si el usuario ya existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Crear usuario
    try:
        hashed_password = auth_manager.hash_password(data['password'])
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            name=data.get('name', data['username'])
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generar token
        token = auth_manager.generate_token(user.id)
        
        # Registrar actividad
        log = ActivityLog(
            user_id=user.id,
            action='user_registered',
            entity_type='user',
            entity_id=user.id,
            details={
                'username': user.username,
                'email': user.email,
                'registration_ip': client_ip
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token,
            'password_strength': password_validation['strength']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/auth/login', methods=['POST'])
@validate_input({
    'required': ['username', 'password'],
    'types': {'username': str, 'password': str}
})
def login():
    """Iniciar sesión con validaciones de seguridad"""
    data = request.validated_data
    client_ip = request.remote_addr
    
    # Verificar rate limiting
    rate_check = auth_manager.rate_limit_check(f"login_{client_ip}")
    
    if not rate_check['allowed']:
        return jsonify({
            'error': 'Too many login attempts. Please try again later.',
            'reset_time': rate_check['reset_time'].isoformat()
        }), 429
    
    # Buscar usuario por username o email
    user = User.query.filter(
        (User.username == data['username']) | (User.email == data['username'])
    ).first()
    
    if not user:
        auth_manager.record_attempt(f"login_{client_ip}")
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Verificar contraseña
    if not user.password_hash or not auth_manager.verify_password(data['password'], user.password_hash):
        auth_manager.record_attempt(f"login_{client_ip}")
        
        # Registrar intento fallido
        log = ActivityLog(
            user_id=user.id,
            action='login_failed',
            entity_type='user',
            entity_id=user.id,
            details={
                'username': data['username'],
                'ip_address': client_ip,
                'reason': 'invalid_password'
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Login exitoso
    try:
        # Generar token
        token = auth_manager.generate_token(user.id)
        
        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Registrar actividad
        log = ActivityLog(
            user_id=user.id,
            action='user_login',
            entity_type='user',
            entity_id=user.id,
            details={
                'username': user.username,
                'ip_address': client_ip,
                'user_agent': request.headers.get('User-Agent', '')
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token,
            'expires_in': 24 * 3600  # 24 horas en segundos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Cerrar sesión"""
    user = request.current_user
    
    # Registrar actividad
    log = ActivityLog(
        user_id=user.id,
        action='user_logout',
        entity_type='user',
        entity_id=user.id,
        details={
            'username': user.username,
            'ip_address': request.remote_addr
        }
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Obtener perfil del usuario autenticado"""
    user = request.current_user
    return jsonify({
        'user': user.to_dict(),
        'last_activity': user.last_login.isoformat() if user.last_login else None
    }), 200

@auth_bp.route('/auth/profile', methods=['PUT'])
@require_auth
@validate_input({
    'types': {'name': str, 'email': str}
})
def update_profile():
    """Actualizar perfil del usuario"""
    user = request.current_user
    data = request.validated_data
    
    # Validar email si se proporciona
    if 'email' in data:
        if not auth_manager.validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Verificar que el email no esté en uso por otro usuario
        existing_user = User.query.filter(
            User.email == data['email'],
            User.id != user.id
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 409
    
    try:
        # Actualizar campos
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Registrar actividad
        log = ActivityLog(
            user_id=user.id,
            action='profile_updated',
            entity_type='user',
            entity_id=user.id,
            details={
                'updated_fields': list(data.keys()),
                'ip_address': request.remote_addr
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/auth/change-password', methods=['POST'])
@require_auth
@validate_input({
    'required': ['current_password', 'new_password'],
    'types': {'current_password': str, 'new_password': str}
})
def change_password():
    """Cambiar contraseña del usuario"""
    user = request.current_user
    data = request.validated_data
    
    # Verificar contraseña actual
    if not user.password_hash or not auth_manager.verify_password(data['current_password'], user.password_hash):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validar nueva contraseña
    password_validation = auth_manager.validate_password_strength(data['new_password'])
    if not password_validation['valid']:
        return jsonify({
            'error': 'New password does not meet security requirements',
            'details': password_validation['errors']
        }), 400
    
    # Verificar que la nueva contraseña sea diferente
    if auth_manager.verify_password(data['new_password'], user.password_hash):
        return jsonify({'error': 'New password must be different from current password'}), 400
    
    try:
        # Actualizar contraseña
        user.password_hash = auth_manager.hash_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Registrar actividad
        log = ActivityLog(
            user_id=user.id,
            action='password_changed',
            entity_type='user',
            entity_id=user.id,
            details={
                'ip_address': request.remote_addr,
                'password_strength': password_validation['strength']
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully',
            'password_strength': password_validation['strength']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/auth/verify-token', methods=['POST'])
def verify_token():
    """Verificar validez de un token JWT"""
    token = request.json.get('token') if request.is_json else None
    
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    payload = auth_manager.verify_token(token)
    
    if 'error' in payload:
        return jsonify({'valid': False, 'error': payload['error']}), 401
    
    # Verificar que el usuario existe
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'valid': False, 'error': 'User not found'}), 401
    
    return jsonify({
        'valid': True,
        'user_id': payload['user_id'],
        'expires_at': payload['exp']
    }), 200

@auth_bp.route('/auth/security-info', methods=['GET'])
@require_auth
def get_security_info():
    """Obtener información de seguridad del usuario"""
    user = request.current_user
    
    # Obtener actividad reciente
    recent_activity = ActivityLog.query.filter_by(
        user_id=user.id
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return jsonify({
        'user_id': user.id,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'account_created': user.created_at.isoformat(),
        'recent_activity': [
            {
                'action': log.action,
                'timestamp': log.created_at.isoformat(),
                'details': log.details
            }
            for log in recent_activity
        ]
    }), 200

