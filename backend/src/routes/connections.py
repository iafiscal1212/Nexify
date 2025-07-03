from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.contact import Contact, SocialProfile, Connection
from src.models.analytics import ActivityLog, AIAnalysis
from src.utils.ai_engine import AIEngine
from datetime import datetime
import time

connections_bp = Blueprint('connections', __name__)
ai_engine = AIEngine()

@connections_bp.route('/connections', methods=['GET'])
def get_connections():
    """Obtener todas las conexiones sugeridas para un usuario"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    status = request.args.get('status', 'pending')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Connection.query.filter_by(user_id=user_id)
    
    if status and status != 'all':
        query = query.filter_by(status=status)
    
    connections = query.order_by(Connection.confidence_score.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'connections': [connection.to_dict() for connection in connections.items],
        'total': connections.total,
        'pages': connections.pages,
        'current_page': page
    })

@connections_bp.route('/connections/<int:connection_id>/status', methods=['PUT'])
def update_connection_status(connection_id):
    """Actualizar el estado de una conexión sugerida"""
    connection = Connection.query.get_or_404(connection_id)
    data = request.json
    
    if 'status' not in data:
        return jsonify({'error': 'status is required'}), 400
    
    valid_statuses = ['pending', 'accepted', 'rejected', 'contacted']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'status must be one of: {", ".join(valid_statuses)}'}), 400
    
    old_status = connection.status
    connection.status = data['status']
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=connection.user_id,
        action='connection_status_updated',
        entity_type='connection',
        entity_id=connection.id,
        details={
            'old_status': old_status,
            'new_status': data['status'],
            'contact_name': connection.contact.name,
            'suggested_contact_name': connection.suggested_contact.name
        }
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify(connection.to_dict())

@connections_bp.route('/connections/generate', methods=['POST'])
def generate_connections():
    """Generar nuevas sugerencias de conexiones usando IA avanzada"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    start_time = time.time()
    
    # Obtener todos los contactos del usuario con sus perfiles sociales
    contacts = Contact.query.filter_by(user_id=user_id).all()
    
    if len(contacts) < 2:
        return jsonify({'error': 'At least 2 contacts are required to generate suggestions'}), 400
    
    # Convertir contactos a diccionarios para el motor de IA
    contacts_data = []
    for contact in contacts:
        contact_dict = contact.to_dict()
        contacts_data.append(contact_dict)
    
    # Generar sugerencias usando el motor de IA avanzado
    suggestions = []
    analysis_results = []
    
    for i, contact1 in enumerate(contacts):
        for j, contact2 in enumerate(contacts[i+1:], i+1):
            # Usar el motor de IA para analizar similitud
            contact1_dict = contacts_data[i]
            contact2_dict = contacts_data[j]
            
            analysis = ai_engine.analyze_contact_similarity(contact1_dict, contact2_dict)
            
            if analysis['similarity_score'] >= 0.3:  # Umbral mínimo de confianza
                # Verificar si ya existe esta sugerencia
                existing = Connection.query.filter_by(
                    user_id=user_id,
                    contact_id=contact1.id,
                    suggested_contact_id=contact2.id
                ).first()
                
                if not existing:
                    # Generar razonamiento usando IA
                    reasoning = ai_engine.generate_connection_reasoning(
                        contact1_dict, contact2_dict, analysis
                    )
                    
                    # Determinar tipo de conexión basado en factores
                    connection_type = determine_connection_type_from_analysis(analysis)
                    
                    suggestion = Connection(
                        user_id=user_id,
                        contact_id=contact1.id,
                        suggested_contact_id=contact2.id,
                        connection_type=connection_type,
                        confidence_score=analysis['similarity_score'],
                        reasoning=reasoning,
                        status='pending'
                    )
                    suggestions.append(suggestion)
                    analysis_results.append(analysis)
    
    # Guardar sugerencias en la base de datos
    for suggestion in suggestions:
        db.session.add(suggestion)
    
    db.session.commit()
    
    processing_time = time.time() - start_time
    
    # Calcular métricas del análisis
    avg_confidence = sum(s.confidence_score for s in suggestions) / len(suggestions) if suggestions else 0
    high_confidence_count = len([s for s in suggestions if s.confidence_score >= 0.7])
    
    # Registrar análisis de IA
    analysis = AIAnalysis(
        user_id=user_id,
        analysis_type='connection_suggestion_advanced',
        input_data={
            'total_contacts': len(contacts),
            'ai_engine_version': 'nexify_ai_v2.0'
        },
        output_data={
            'suggestions_generated': len(suggestions),
            'high_confidence_suggestions': high_confidence_count,
            'avg_confidence_score': avg_confidence,
            'analysis_results': analysis_results[:5]  # Guardar solo los primeros 5 para no sobrecargar
        },
        confidence_score=avg_confidence,
        processing_time=processing_time,
        model_version='nexify_ai_v2.0'
    )
    db.session.add(analysis)
    db.session.commit()
    
    # Registrar actividad
    log = ActivityLog(
        user_id=user_id,
        action='connections_generated_ai',
        entity_type='connection',
        details={
            'suggestions_count': len(suggestions),
            'high_confidence_count': high_confidence_count,
            'avg_confidence': avg_confidence
        }
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': f'Generated {len(suggestions)} connection suggestions using advanced AI',
        'suggestions_count': len(suggestions),
        'high_confidence_count': high_confidence_count,
        'avg_confidence_score': avg_confidence,
        'processing_time': processing_time,
        'ai_insights': {
            'total_analyzed_pairs': len(contacts) * (len(contacts) - 1) // 2,
            'suggestions_generated': len(suggestions),
            'success_rate': len(suggestions) / (len(contacts) * (len(contacts) - 1) // 2) if len(contacts) > 1 else 0
        },
        'suggestions': [s.to_dict() for s in suggestions[:10]]  # Mostrar solo las primeras 10
    })

def determine_connection_type_from_analysis(analysis):
    """Determina el tipo de conexión basado en el análisis de IA"""
    factors = analysis.get('factors', [])
    
    if any('Industria' in factor for factor in factors):
        if any('Ubicación' in factor for factor in factors):
            return 'industry_location_match'
        return 'industry_match'
    elif any('Ubicación' in factor for factor in factors):
        return 'location_match'
    elif any('Empresa' in factor for factor in factors):
        return 'company_match'
    elif any('social' in factor for factor in factors):
        return 'social_match'
    else:
        return 'ai_recommended'

@connections_bp.route('/connections/analyze-network', methods=['POST'])
def analyze_network():
    """Analizar la salud de la red usando IA"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    start_time = time.time()
    
    # Obtener contactos
    contacts = Contact.query.filter_by(user_id=user_id).all()
    contacts_data = [contact.to_dict() for contact in contacts]
    
    # Analizar salud de la red
    network_analysis = ai_engine.analyze_network_health(contacts_data)
    
    processing_time = time.time() - start_time
    
    # Registrar análisis
    analysis = AIAnalysis(
        user_id=user_id,
        analysis_type='network_health_analysis',
        input_data={'total_contacts': len(contacts)},
        output_data=network_analysis,
        confidence_score=0.95,
        processing_time=processing_time,
        model_version='nexify_ai_v2.0'
    )
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify({
        'analysis_id': analysis.id,
        'network_health': network_analysis,
        'processing_time': processing_time
    })

@connections_bp.route('/connections/stats', methods=['GET'])
def get_connections_stats():
    """Obtener estadísticas de conexiones"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Estadísticas por estado
    status_stats = db.session.query(
        Connection.status,
        db.func.count(Connection.id).label('count')
    ).filter_by(user_id=user_id).group_by(Connection.status).all()
    
    # Estadísticas por tipo de conexión
    type_stats = db.session.query(
        Connection.connection_type,
        db.func.count(Connection.id).label('count'),
        db.func.avg(Connection.confidence_score).label('avg_score')
    ).filter_by(user_id=user_id).group_by(Connection.connection_type).all()
    
    # Score promedio
    avg_score = db.session.query(
        db.func.avg(Connection.confidence_score)
    ).filter_by(user_id=user_id).scalar() or 0
    
    # Estadísticas de IA
    ai_analyses = AIAnalysis.query.filter_by(
        user_id=user_id,
        analysis_type='connection_suggestion_advanced'
    ).order_by(AIAnalysis.created_at.desc()).limit(5).all()
    
    return jsonify({
        'by_status': [{'status': stat[0], 'count': stat[1]} for stat in status_stats],
        'by_type': [{'type': stat[0], 'count': stat[1], 'avg_score': float(stat[2])} for stat in type_stats],
        'average_confidence_score': float(avg_score),
        'recent_ai_analyses': [analysis.to_dict() for analysis in ai_analyses]
    })

@connections_bp.route('/connections/export', methods=['GET'])
def export_connections():
    """Exportar conexiones en formato JSON"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    status = request.args.get('status')
    
    query = Connection.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    
    connections = query.all()
    
    export_data = {
        'export_date': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'total_connections': len(connections),
        'ai_engine_version': 'nexify_ai_v2.0',
        'connections': [connection.to_dict() for connection in connections]
    }
    
    return jsonify(export_data)

