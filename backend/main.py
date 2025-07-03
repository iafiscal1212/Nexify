import os
import sys

# Agregar el directorio actual al path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.contacts import contacts_bp
from src.routes.connections import connections_bp
from src.routes.analytics import analytics_bp
from src.routes.auth import auth_bp
from src.utils.auth import auth_manager

app = Flask(__name__, static_folder=os.path.join(current_dir, 'src', 'static'))

# Configuración de seguridad
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexify-secret-key-2024-super-secure')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'nexify-jwt-secret-key-2024-super-secure')

# Configuración de CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*')
CORS(app, origins=cors_origins.split(',') if cors_origins != '*' else '*')

# Configuración de base de datos
database_path = os.path.join(current_dir, 'src', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(connections_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')

# Inicializar auth manager
auth_manager.init_app(app)

# Crear tablas
with app.app_context():
    db.create_all()

# Ruta para servir el frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')

# Endpoint de salud
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'features': {
            'authentication': True,
            'ai_suggestions': True,
            'analytics': True,
            'security': True
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

