"""
Motor de IA avanzado para NEXIFY
Incluye algoritmos mejorados para análisis de contactos y sugerencias de conexiones
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

class AIEngine:
    """Motor de IA para análisis de contactos y sugerencias de conexiones"""
    
    def __init__(self):
        self.industry_keywords = {
            'tecnología': ['tech', 'software', 'desarrollo', 'programación', 'ai', 'ia', 'datos', 'digital'],
            'marketing': ['marketing', 'publicidad', 'social media', 'contenido', 'branding'],
            'finanzas': ['finanzas', 'banca', 'inversión', 'contabilidad', 'economía'],
            'salud': ['salud', 'medicina', 'farmacia', 'hospital', 'clínica'],
            'educación': ['educación', 'universidad', 'enseñanza', 'formación', 'academia'],
            'consultoría': ['consultoría', 'asesoría', 'estrategia', 'gestión', 'negocios']
        }
        
        self.platform_weights = {
            'linkedin': 1.0,    # Más peso para LinkedIn (profesional)
            'facebook': 0.7,    # Peso medio para Facebook
            'instagram': 0.8,   # Buen peso para Instagram
            'tiktok': 0.6       # Menor peso para TikTok (más personal)
        }
    
    def analyze_contact_similarity(self, contact1: Dict, contact2: Dict) -> Dict:
        """Analiza la similitud entre dos contactos"""
        
        similarity_score = 0.0
        factors = []
        
        # Factor 1: Industria (peso: 0.3)
        industry_score = self._calculate_industry_similarity(contact1, contact2)
        similarity_score += industry_score * 0.3
        if industry_score > 0:
            factors.append(f"Industria similar ({industry_score:.2f})")
        
        # Factor 2: Ubicación (peso: 0.25)
        location_score = self._calculate_location_similarity(contact1, contact2)
        similarity_score += location_score * 0.25
        if location_score > 0:
            factors.append(f"Ubicación similar ({location_score:.2f})")
        
        # Factor 3: Empresa (peso: 0.2)
        company_score = self._calculate_company_similarity(contact1, contact2)
        similarity_score += company_score * 0.2
        if company_score > 0:
            factors.append(f"Empresa relacionada ({company_score:.2f})")
        
        # Factor 4: Redes sociales (peso: 0.15)
        social_score = self._calculate_social_similarity(contact1, contact2)
        similarity_score += social_score * 0.15
        if social_score > 0:
            factors.append(f"Presencia social similar ({social_score:.2f})")
        
        # Factor 5: Nivel profesional (peso: 0.1)
        level_score = self._calculate_professional_level_similarity(contact1, contact2)
        similarity_score += level_score * 0.1
        if level_score > 0:
            factors.append(f"Nivel profesional similar ({level_score:.2f})")
        
        return {
            'similarity_score': min(similarity_score, 1.0),
            'factors': factors,
            'recommendation_strength': self._get_recommendation_strength(similarity_score)
        }
    
    def _calculate_industry_similarity(self, contact1: Dict, contact2: Dict) -> float:
        """Calcula similitud por industria"""
        industry1 = contact1.get('industry', '').lower()
        industry2 = contact2.get('industry', '').lower()
        
        if not industry1 or not industry2:
            return 0.0
        
        # Coincidencia exacta
        if industry1 == industry2:
            return 1.0
        
        # Buscar palabras clave relacionadas
        for category, keywords in self.industry_keywords.items():
            found1 = any(keyword in industry1 for keyword in keywords)
            found2 = any(keyword in industry2 for keyword in keywords)
            if found1 and found2:
                return 0.7
        
        # Similitud por palabras comunes
        words1 = set(industry1.split())
        words2 = set(industry2.split())
        common_words = words1.intersection(words2)
        
        if common_words:
            return len(common_words) / max(len(words1), len(words2))
        
        return 0.0
    
    def _calculate_location_similarity(self, contact1: Dict, contact2: Dict) -> float:
        """Calcula similitud por ubicación"""
        location1 = contact1.get('location', '').lower()
        location2 = contact2.get('location', '').lower()
        
        if not location1 or not location2:
            return 0.0
        
        # Coincidencia exacta
        if location1 == location2:
            return 1.0
        
        # Buscar ciudades/países comunes
        words1 = set(location1.replace(',', ' ').split())
        words2 = set(location2.replace(',', ' ').split())
        common_words = words1.intersection(words2)
        
        if common_words:
            return 0.8 if len(common_words) >= 2 else 0.5
        
        return 0.0
    
    def _calculate_company_similarity(self, contact1: Dict, contact2: Dict) -> float:
        """Calcula similitud por empresa"""
        company1 = contact1.get('company', '').lower()
        company2 = contact2.get('company', '').lower()
        
        if not company1 or not company2:
            return 0.0
        
        # Misma empresa
        if company1 == company2:
            return 1.0
        
        # Empresas relacionadas (subsidiarias, grupos)
        if company1 in company2 or company2 in company1:
            return 0.6
        
        return 0.0
    
    def _calculate_social_similarity(self, contact1: Dict, contact2: Dict) -> float:
        """Calcula similitud por redes sociales"""
        profiles1 = contact1.get('social_profiles', [])
        profiles2 = contact2.get('social_profiles', [])
        
        if not profiles1 or not profiles2:
            return 0.0
        
        platforms1 = {p.get('platform') for p in profiles1}
        platforms2 = {p.get('platform') for p in profiles2}
        
        common_platforms = platforms1.intersection(platforms2)
        
        if not common_platforms:
            return 0.0
        
        # Calcular score basado en plataformas comunes y sus pesos
        total_weight = 0.0
        common_weight = 0.0
        
        for platform in platforms1.union(platforms2):
            weight = self.platform_weights.get(platform, 0.5)
            total_weight += weight
            if platform in common_platforms:
                common_weight += weight
        
        return common_weight / total_weight if total_weight > 0 else 0.0
    
    def _calculate_professional_level_similarity(self, contact1: Dict, contact2: Dict) -> float:
        """Calcula similitud por nivel profesional"""
        position1 = contact1.get('position', '').lower()
        position2 = contact2.get('position', '').lower()
        
        if not position1 or not position2:
            return 0.0
        
        # Niveles jerárquicos
        senior_keywords = ['ceo', 'cto', 'cfo', 'director', 'gerente', 'manager', 'lead', 'senior']
        mid_keywords = ['analista', 'especialista', 'coordinator', 'supervisor']
        junior_keywords = ['junior', 'asistente', 'trainee', 'intern']
        
        level1 = self._get_professional_level(position1, senior_keywords, mid_keywords, junior_keywords)
        level2 = self._get_professional_level(position2, senior_keywords, mid_keywords, junior_keywords)
        
        if level1 == level2:
            return 0.8
        elif abs(level1 - level2) == 1:
            return 0.4
        
        return 0.0
    
    def _get_professional_level(self, position: str, senior_kw: List, mid_kw: List, junior_kw: List) -> int:
        """Determina el nivel profesional (0=junior, 1=mid, 2=senior)"""
        if any(keyword in position for keyword in senior_kw):
            return 2
        elif any(keyword in position for keyword in mid_kw):
            return 1
        elif any(keyword in position for keyword in junior_kw):
            return 0
        else:
            return 1  # Default a mid-level
    
    def _get_recommendation_strength(self, score: float) -> str:
        """Determina la fuerza de la recomendación"""
        if score >= 0.8:
            return 'muy_alta'
        elif score >= 0.6:
            return 'alta'
        elif score >= 0.4:
            return 'media'
        elif score >= 0.2:
            return 'baja'
        else:
            return 'muy_baja'
    
    def generate_connection_reasoning(self, contact1: Dict, contact2: Dict, analysis: Dict) -> str:
        """Genera el razonamiento para la sugerencia de conexión"""
        factors = analysis.get('factors', [])
        score = analysis.get('similarity_score', 0)
        
        if not factors:
            return "Perfiles complementarios que podrían beneficiarse de una conexión profesional."
        
        reasoning_parts = []
        
        # Agregar contexto basado en los factores
        if any('Industria' in factor for factor in factors):
            reasoning_parts.append(f"Ambos profesionales trabajan en {contact1.get('industry', 'la misma industria')}")
        
        if any('Ubicación' in factor for factor in factors):
            reasoning_parts.append(f"Se encuentran en la misma ubicación geográfica ({contact1.get('location', 'ubicación similar')})")
        
        if any('Empresa' in factor for factor in factors):
            reasoning_parts.append("Tienen conexiones empresariales relacionadas")
        
        if any('social' in factor for factor in factors):
            reasoning_parts.append("Comparten presencia en plataformas sociales similares")
        
        # Agregar recomendación basada en el score
        if score >= 0.7:
            reasoning_parts.append("Esta conexión tiene un alto potencial de éxito y beneficio mutuo")
        elif score >= 0.5:
            reasoning_parts.append("Existe una buena oportunidad de colaboración profesional")
        else:
            reasoning_parts.append("Podría ser una conexión valiosa para expandir la red profesional")
        
        return ". ".join(reasoning_parts) + "."
    
    def analyze_network_health(self, contacts: List[Dict]) -> Dict:
        """Analiza la salud general de la red de contactos"""
        if not contacts:
            return {
                'health_score': 0.0,
                'diversity_index': 0.0,
                'connection_potential': 0.0,
                'recommendations': ['Agregar contactos para comenzar el análisis']
            }
        
        # Calcular diversidad de industrias
        industries = [c.get('industry') for c in contacts if c.get('industry')]
        diversity_index = len(set(industries)) / len(contacts) if contacts else 0
        
        # Calcular potencial de conexiones
        total_possible_connections = len(contacts) * (len(contacts) - 1) / 2
        high_potential_connections = 0
        
        for i, contact1 in enumerate(contacts):
            for contact2 in contacts[i+1:]:
                analysis = self.analyze_contact_similarity(contact1, contact2)
                if analysis['similarity_score'] >= 0.5:
                    high_potential_connections += 1
        
        connection_potential = high_potential_connections / total_possible_connections if total_possible_connections > 0 else 0
        
        # Score general de salud
        health_score = (diversity_index * 0.4 + connection_potential * 0.6)
        
        # Generar recomendaciones
        recommendations = self._generate_network_recommendations(contacts, diversity_index, connection_potential)
        
        return {
            'health_score': health_score,
            'diversity_index': diversity_index,
            'connection_potential': connection_potential,
            'total_contacts': len(contacts),
            'unique_industries': len(set(industries)),
            'recommendations': recommendations
        }
    
    def _generate_network_recommendations(self, contacts: List[Dict], diversity: float, potential: float) -> List[str]:
        """Genera recomendaciones para mejorar la red"""
        recommendations = []
        
        if len(contacts) < 10:
            recommendations.append("Considera agregar más contactos para una red más robusta (objetivo: 10+ contactos)")
        
        if diversity < 0.3:
            recommendations.append("Diversifica tu red agregando contactos de diferentes industrias")
        
        if potential < 0.2:
            recommendations.append("Busca contactos con más puntos en común para facilitar conexiones")
        
        # Analizar ubicaciones
        locations = [c.get('location') for c in contacts if c.get('location')]
        if len(set(locations)) < 3:
            recommendations.append("Expande tu red geográficamente para acceder a más oportunidades")
        
        # Analizar presencia social
        social_contacts = [c for c in contacts if c.get('social_profiles')]
        if len(social_contacts) / len(contacts) < 0.5:
            recommendations.append("Agrega perfiles sociales a más contactos para mejorar las sugerencias de IA")
        
        if not recommendations:
            recommendations.append("Tu red está bien balanceada. Continúa agregando contactos de calidad.")
        
        return recommendations

