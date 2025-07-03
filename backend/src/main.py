import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.contacts import contacts_bp
from src.routes.connections import connections_bp
from src.routes.analytics import analytics_bp
from src.routes.auth import auth_bp
from src.utils.auth import auth_manager

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuración de seguridad
app.config['SECRET_KEY'] = 'nexify-secret-key-2024-super-secure'
app.config['JWT_SECRET_KEY'] = 'nexify-jwt-secret-key-2024-super-secure'
app.config['JWT_EXPIRATION_HOURS'] = 24
app.config['PASSWORD_MIN_LENGTH'] = 8
app.config['MAX_LOGIN_ATTEMPTS'] = 5

# Habilitar CORS para todas las rutas
CORS(app, origins="*")

# Inicializar gestor de autenticación
auth_manager.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(connections_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Importar todos los modelos para que se creen las tablas
from src.models.contact import Contact, SocialProfile, Connection
from src.models.analytics import AIAnalysis, NetworkMetrics, ActivityLog

with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Endpoint de salud para verificar que la API funciona
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'NEXIFY Backend',
        'version': '2.0.0',
        'features': ['AI Engine v2.0', 'Advanced Security', 'JWT Authentication'],
        'security': {
            'jwt_enabled': True,
            'password_requirements': {
                'min_length': app.config['PASSWORD_MIN_LENGTH'],
                'requires_uppercase': True,
                'requires_lowercase': True,
                'requires_number': True,
                'requires_special_char': True
            },
            'rate_limiting': {
                'max_login_attempts': app.config['MAX_LOGIN_ATTEMPTS'],
                'window_minutes': 15
            }
        }
    })

# Manejo de errores de seguridad
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access. Please login.'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access forbidden.'}), 403

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

