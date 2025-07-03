from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # 'contact_mapping', 'connection_suggestion', 'network_analysis'
    input_data = db.Column(db.JSON, nullable=True)  # Datos de entrada para el análisis
    output_data = db.Column(db.JSON, nullable=True)  # Resultados del análisis
    confidence_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)  # Tiempo en segundos
    model_version = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIAnalysis {self.analysis_type} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'analysis_type': self.analysis_type,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NetworkMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_contacts = db.Column(db.Integer, default=0)
    total_connections = db.Column(db.Integer, default=0)
    pending_suggestions = db.Column(db.Integer, default=0)
    accepted_suggestions = db.Column(db.Integer, default=0)
    network_density = db.Column(db.Float, nullable=True)  # Densidad de la red de contactos
    avg_connection_strength = db.Column(db.Float, nullable=True)
    top_industries = db.Column(db.JSON, nullable=True)  # Lista de industrias principales
    top_locations = db.Column(db.JSON, nullable=True)  # Lista de ubicaciones principales
    social_platforms_coverage = db.Column(db.JSON, nullable=True)  # Cobertura por plataforma
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NetworkMetrics for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_contacts': self.total_contacts,
            'total_connections': self.total_connections,
            'pending_suggestions': self.pending_suggestions,
            'accepted_suggestions': self.accepted_suggestions,
            'network_density': self.network_density,
            'avg_connection_strength': self.avg_connection_strength,
            'top_industries': self.top_industries,
            'top_locations': self.top_locations,
            'social_platforms_coverage': self.social_platforms_coverage,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'contact_added', 'connection_suggested', 'connection_accepted', etc.
    entity_type = db.Column(db.String(50), nullable=True)  # 'contact', 'connection', 'social_profile'
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ActivityLog {self.action} by user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

