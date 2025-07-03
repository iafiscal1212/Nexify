from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.contact import Contact, SocialProfile, Connection
from src.models.analytics import AIAnalysis, NetworkMetrics, ActivityLog
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_data():
    """Obtener datos del dashboard principal"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Métricas básicas
    total_contacts = Contact.query.filter_by(user_id=user_id).count()
    total_connections = Connection.query.filter_by(user_id=user_id).count()
    pending_suggestions = Connection.query.filter_by(user_id=user_id, status='pending').count()
    accepted_connections = Connection.query.filter_by(user_id=user_id, status='accepted').count()
    
    # Actividad reciente (últimos 7 días)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = ActivityLog.query.filter(
        ActivityLog.user_id == user_id,
        ActivityLog.timestamp >= week_ago
    ).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Top industrias
    industry_stats = db.session.query(
        Contact.industry,
        func.count(Contact.id).label('count')
    ).filter(
        Contact.user_id == user_id,
        Contact.industry.isnot(None)
    ).group_by(Contact.industry).order_by(func.count(Contact.id).desc()).limit(5).all()
    
    # Distribución por plataformas sociales
    platform_stats = db.session.query(
        SocialProfile.platform,
        func.count(SocialProfile.id).label('count')
    ).join(Contact).filter(
        Contact.user_id == user_id
    ).group_by(SocialProfile.platform).all()
    
    # Score promedio de conexiones
    avg_connection_score = db.session.query(
        func.avg(Connection.confidence_score)
    ).filter_by(user_id=user_id).scalar() or 0
    
    return jsonify({
        'summary': {
            'total_contacts': total_contacts,
            'total_connections': total_connections,
            'pending_suggestions': pending_suggestions,
            'accepted_connections': accepted_connections,
            'avg_connection_score': float(avg_connection_score)
        },
        'recent_activity': [activity.to_dict() for activity in recent_activity],
        'top_industries': [{'industry': stat[0], 'count': stat[1]} for stat in industry_stats],
        'platform_distribution': [{'platform': stat[0], 'count': stat[1]} for stat in platform_stats]
    })

@analytics_bp.route('/analytics/network-analysis', methods=['POST'])
def analyze_network():
    """Realizar análisis completo de la red de contactos"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    start_time = datetime.utcnow()
    
    # Obtener todos los contactos
    contacts = Contact.query.filter_by(user_id=user_id).all()
    
    if not contacts:
        return jsonify({'error': 'No contacts found for analysis'}), 400
    
    # Calcular métricas de red
    analysis_results = {
        'total_contacts': len(contacts),
        'network_density': calculate_network_density(contacts),
        'industry_diversity': calculate_industry_diversity(contacts),
        'geographic_spread': calculate_geographic_spread(contacts),
        'social_media_coverage': calculate_social_media_coverage(contacts),
        'connection_opportunities': identify_connection_opportunities(contacts),
        'influence_metrics': calculate_influence_metrics(contacts)
    }
    
    # Guardar análisis
    analysis = AIAnalysis(
        user_id=user_id,
        analysis_type='network_analysis',
        input_data={'contacts_analyzed': len(contacts)},
        output_data=analysis_results,
        confidence_score=0.95,  # Alta confianza en análisis estadístico
        processing_time=(datetime.utcnow() - start_time).total_seconds(),
        model_version='nexify_analytics_v1.0'
    )
    db.session.add(analysis)
    
    # Actualizar métricas de red
    metrics = NetworkMetrics.query.filter_by(user_id=user_id).first()
    if not metrics:
        metrics = NetworkMetrics(user_id=user_id)
    
    metrics.total_contacts = analysis_results['total_contacts']
    metrics.network_density = analysis_results['network_density']
    metrics.top_industries = analysis_results['industry_diversity']['top_industries']
    metrics.top_locations = analysis_results['geographic_spread']['top_locations']
    metrics.social_platforms_coverage = analysis_results['social_media_coverage']
    metrics.last_calculated = datetime.utcnow()
    
    db.session.add(metrics)
    db.session.commit()
    
    return jsonify({
        'analysis_id': analysis.id,
        'results': analysis_results,
        'recommendations': generate_network_recommendations(analysis_results)
    })

def calculate_network_density(contacts):
    """Calcular la densidad de la red de contactos"""
    if len(contacts) < 2:
        return 0.0
    
    # Contar conexiones potenciales basadas en industria, ubicación, empresa
    connections = 0
    total_possible = len(contacts) * (len(contacts) - 1) / 2
    
    for i, contact1 in enumerate(contacts):
        for contact2 in contacts[i+1:]:
            if (contact1.industry and contact2.industry and contact1.industry == contact2.industry) or \
               (contact1.location and contact2.location and contact1.location == contact2.location) or \
               (contact1.company and contact2.company and contact1.company == contact2.company):
                connections += 1
    
    return connections / total_possible if total_possible > 0 else 0.0

def calculate_industry_diversity(contacts):
    """Calcular diversidad de industrias"""
    industries = {}
    for contact in contacts:
        if contact.industry:
            industries[contact.industry] = industries.get(contact.industry, 0) + 1
    
    total_with_industry = sum(industries.values())
    diversity_score = len(industries) / total_with_industry if total_with_industry > 0 else 0
    
    top_industries = sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'diversity_score': diversity_score,
        'total_industries': len(industries),
        'top_industries': [{'industry': ind, 'count': count} for ind, count in top_industries]
    }

def calculate_geographic_spread(contacts):
    """Calcular distribución geográfica"""
    locations = {}
    for contact in contacts:
        if contact.location:
            locations[contact.location] = locations.get(contact.location, 0) + 1
    
    total_with_location = sum(locations.values())
    spread_score = len(locations) / total_with_location if total_with_location > 0 else 0
    
    top_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'spread_score': spread_score,
        'total_locations': len(locations),
        'top_locations': [{'location': loc, 'count': count} for loc, count in top_locations]
    }

def calculate_social_media_coverage(contacts):
    """Calcular cobertura en redes sociales"""
    platform_coverage = {'tiktok': 0, 'instagram': 0, 'facebook': 0, 'linkedin': 0}
    total_profiles = 0
    
    for contact in contacts:
        contact_platforms = set()
        for profile in contact.social_profiles:
            if profile.platform in platform_coverage:
                contact_platforms.add(profile.platform)
                total_profiles += 1
        
        for platform in contact_platforms:
            platform_coverage[platform] += 1
    
    total_contacts = len(contacts)
    coverage_percentages = {
        platform: (count / total_contacts * 100) if total_contacts > 0 else 0
        for platform, count in platform_coverage.items()
    }
    
    return {
        'platform_counts': platform_coverage,
        'coverage_percentages': coverage_percentages,
        'total_profiles': total_profiles,
        'avg_platforms_per_contact': total_profiles / total_contacts if total_contacts > 0 else 0
    }

def identify_connection_opportunities(contacts):
    """Identificar oportunidades de conexión"""
    opportunities = []
    
    # Agrupar por industria
    by_industry = {}
    for contact in contacts:
        if contact.industry:
            if contact.industry not in by_industry:
                by_industry[contact.industry] = []
            by_industry[contact.industry].append(contact)
    
    # Identificar industrias con múltiples contactos
    for industry, industry_contacts in by_industry.items():
        if len(industry_contacts) >= 3:
            opportunities.append({
                'type': 'industry_cluster',
                'industry': industry,
                'contact_count': len(industry_contacts),
                'potential_connections': len(industry_contacts) * (len(industry_contacts) - 1) / 2
            })
    
    return opportunities

def calculate_influence_metrics(contacts):
    """Calcular métricas de influencia"""
    total_followers = 0
    verified_count = 0
    high_engagement_count = 0
    
    for contact in contacts:
        for profile in contact.social_profiles:
            if profile.followers_count:
                total_followers += profile.followers_count
            if profile.verified:
                verified_count += 1
            if profile.engagement_rate and profile.engagement_rate > 0.05:  # 5% engagement
                high_engagement_count += 1
    
    return {
        'total_network_reach': total_followers,
        'verified_profiles': verified_count,
        'high_engagement_profiles': high_engagement_count,
        'avg_followers_per_contact': total_followers / len(contacts) if contacts else 0
    }

def generate_network_recommendations(analysis_results):
    """Generar recomendaciones basadas en el análisis"""
    recommendations = []
    
    # Recomendación de diversidad
    if analysis_results['industry_diversity']['diversity_score'] < 0.3:
        recommendations.append({
            'type': 'diversify_industries',
            'priority': 'high',
            'message': 'Considera expandir tu red a diferentes industrias para aumentar oportunidades de colaboración.'
        })
    
    # Recomendación geográfica
    if analysis_results['geographic_spread']['spread_score'] < 0.2:
        recommendations.append({
            'type': 'expand_geographically',
            'priority': 'medium',
            'message': 'Amplía tu red geográficamente para acceder a mercados y oportunidades globales.'
        })
    
    # Recomendación de redes sociales
    coverage = analysis_results['social_media_coverage']['coverage_percentages']
    low_coverage_platforms = [platform for platform, percentage in coverage.items() if percentage < 50]
    
    if low_coverage_platforms:
        recommendations.append({
            'type': 'improve_social_coverage',
            'priority': 'medium',
            'message': f'Mejora la cobertura en: {", ".join(low_coverage_platforms)} para maximizar tu alcance digital.'
        })
    
    return recommendations

@analytics_bp.route('/analytics/trends', methods=['GET'])
def get_trends():
    """Obtener tendencias de crecimiento de la red"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Tendencia de contactos agregados
    contact_trend = db.session.query(
        func.date(Contact.created_at).label('date'),
        func.count(Contact.id).label('count')
    ).filter(
        Contact.user_id == user_id,
        Contact.created_at >= start_date
    ).group_by(func.date(Contact.created_at)).all()
    
    # Tendencia de actividad
    activity_trend = db.session.query(
        func.date(ActivityLog.timestamp).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.timestamp >= start_date
    ).group_by(func.date(ActivityLog.timestamp)).all()
    
    return jsonify({
        'contact_growth': [{'date': str(trend[0]), 'count': trend[1]} for trend in contact_trend],
        'activity_trend': [{'date': str(trend[0]), 'count': trend[1]} for trend in activity_trend]
    })

@analytics_bp.route('/analytics/export', methods=['GET'])
def export_analytics():
    """Exportar datos de análisis"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Obtener métricas más recientes
    metrics = NetworkMetrics.query.filter_by(user_id=user_id).first()
    
    # Obtener análisis recientes
    recent_analyses = AIAnalysis.query.filter_by(user_id=user_id).order_by(
        AIAnalysis.created_at.desc()
    ).limit(10).all()
    
    export_data = {
        'export_date': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'current_metrics': metrics.to_dict() if metrics else None,
        'recent_analyses': [analysis.to_dict() for analysis in recent_analyses]
    }
    
    return jsonify(export_data)

