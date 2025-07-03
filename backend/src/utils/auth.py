"""
Sistema de autenticación y seguridad para NEXIFY
Incluye JWT tokens, validación de entrada y medidas de seguridad
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from src.models.user import User

class AuthManager:
    """Gestor de autenticación y seguridad"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar el gestor con la aplicación Flask"""
        app.config.setdefault('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        app.config.setdefault('JWT_EXPIRATION_HOURS', 24)
        app.config.setdefault('PASSWORD_MIN_LENGTH', 8)
        app.config.setdefault('MAX_LOGIN_ATTEMPTS', 5)
    
    def hash_password(self, password: str) -> str:
        """Hash de contraseña usando SHA-256 con salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verificar contraseña contra hash"""
        try:
            salt, stored_hash = hashed_password.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except ValueError:
            return False
    
    def generate_token(self, user_id: int) -> str:
        """Generar JWT token para usuario"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
    
    def verify_token(self, token: str) -> dict:
        """Verificar y decodificar JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def validate_password_strength(self, password: str) -> dict:
        """Validar fortaleza de contraseña"""
        errors = []
        
        if len(password) < current_app.config['PASSWORD_MIN_LENGTH']:
            errors.append(f"Password must be at least {current_app.config['PASSWORD_MIN_LENGTH']} characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """Calcular fortaleza de contraseña"""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        if score <= 2:
            return 'weak'
        elif score <= 4:
            return 'medium'
        else:
            return 'strong'
    
    def validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def sanitize_input(self, data: str) -> str:
        """Sanitizar entrada de usuario"""
        if not isinstance(data, str):
            return data
        
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        # Limitar longitud
        return data[:1000]  # Máximo 1000 caracteres
    
    def rate_limit_check(self, identifier: str, max_attempts: int = None, window_minutes: int = 15) -> dict:
        """Verificar límite de intentos (implementación básica en memoria)"""
        # En producción, esto debería usar Redis o una base de datos
        if not hasattr(self, '_rate_limits'):
            self._rate_limits = {}
        
        if max_attempts is None:
            max_attempts = current_app.config['MAX_LOGIN_ATTEMPTS']
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Limpiar intentos antiguos
        if identifier in self._rate_limits:
            self._rate_limits[identifier] = [
                attempt for attempt in self._rate_limits[identifier]
                if attempt > window_start
            ]
        else:
            self._rate_limits[identifier] = []
        
        # Verificar límite
        attempts = len(self._rate_limits[identifier])
        
        if attempts >= max_attempts:
            return {
                'allowed': False,
                'attempts': attempts,
                'reset_time': window_start + timedelta(minutes=window_minutes)
            }
        
        return {
            'allowed': True,
            'attempts': attempts,
            'remaining': max_attempts - attempts
        }
    
    def record_attempt(self, identifier: str):
        """Registrar intento de autenticación"""
        if not hasattr(self, '_rate_limits'):
            self._rate_limits = {}
        
        if identifier not in self._rate_limits:
            self._rate_limits[identifier] = []
        
        self._rate_limits[identifier].append(datetime.utcnow())

# Decorador para requerir autenticación
def require_auth(f):
    """Decorador para requerir autenticación JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Buscar token en header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is required'}), 401
        
        # Verificar token
        auth_manager = AuthManager()
        payload = auth_manager.verify_token(token)
        
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401
        
        # Verificar que el usuario existe
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Agregar usuario al contexto de la request
        request.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function

# Decorador para validar entrada
def validate_input(schema):
    """Decorador para validar entrada JSON"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Validar campos requeridos
            for field in schema.get('required', []):
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Validar tipos de datos
            for field, field_type in schema.get('types', {}).items():
                if field in data and not isinstance(data[field], field_type):
                    return jsonify({'error': f'Field {field} must be of type {field_type.__name__}'}), 400
            
            # Sanitizar entrada
            auth_manager = AuthManager()
            for field in data:
                if isinstance(data[field], str):
                    data[field] = auth_manager.sanitize_input(data[field])
            
            request.validated_data = data
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Instancia global del gestor de autenticación
auth_manager = AuthManager()

