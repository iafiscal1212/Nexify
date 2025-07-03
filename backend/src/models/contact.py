from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    social_profiles = db.relationship('SocialProfile', backref='contact', lazy=True, cascade='all, delete-orphan')
    connections = db.relationship('Connection', foreign_keys='Connection.contact_id', backref='contact', lazy=True)
    
    def __repr__(self):
        return f'<Contact {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'position': self.position,
            'industry': self.industry,
            'location': self.location,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'social_profiles': [profile.to_dict() for profile in self.social_profiles]
        }

class SocialProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # 'tiktok', 'instagram', 'facebook', 'linkedin'
    username = db.Column(db.String(100), nullable=False)
    profile_url = db.Column(db.String(255), nullable=True)
    followers_count = db.Column(db.Integer, nullable=True)
    following_count = db.Column(db.Integer, nullable=True)
    posts_count = db.Column(db.Integer, nullable=True)
    engagement_rate = db.Column(db.Float, nullable=True)
    verified = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SocialProfile {self.platform}:{self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'platform': self.platform,
            'username': self.username,
            'profile_url': self.profile_url,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'posts_count': self.posts_count,
            'engagement_rate': self.engagement_rate,
            'verified': self.verified,
            'bio': self.bio,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    suggested_contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    connection_type = db.Column(db.String(50), nullable=False)  # 'mutual_connection', 'industry_match', 'location_match', 'interest_match'
    confidence_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    reasoning = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected', 'contacted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con el contacto sugerido
    suggested_contact = db.relationship('Contact', foreign_keys=[suggested_contact_id], backref='suggested_connections')
    
    def __repr__(self):
        return f'<Connection {self.contact_id} -> {self.suggested_contact_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contact_id': self.contact_id,
            'suggested_contact_id': self.suggested_contact_id,
            'connection_type': self.connection_type,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'suggested_contact': self.suggested_contact.to_dict() if self.suggested_contact else None
        }

