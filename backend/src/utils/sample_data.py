"""
Script para poblar la base de datos con datos de ejemplo para testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db
from models.user import User
from models.contact import Contact, SocialProfile
from models.analytics import NetworkMetric, ActivityLog
from werkzeug.security import generate_password_hash

def create_sample_data():
    """Crea datos de ejemplo para testing de la aplicación"""
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        print("🚀 Creando datos de ejemplo para NEXIFY...")
        
        # Verificar si ya existen datos
        if Contact.query.count() > 0:
            print("⚠️ Ya existen datos en la base de datos. Saltando creación de datos de ejemplo.")
            return
        
        # Obtener usuarios existentes (los usuarios deben registrarse a través de la aplicación)
        users = User.query.all()
        if not users:
            print("ℹ️ No hay usuarios registrados. Los contactos se crearán cuando los usuarios se registren.")
            return
        
        # Usar el primer usuario disponible para crear contactos de ejemplo
        user = users[0]
        print(f"✅ Creando contactos para el usuario: {user.username}")
        
        # Datos de contactos de ejemplo
        sample_contacts = [
            {
                "name": "María García",
                "email": "maria.garcia@techcorp.com",
                "company": "TechCorp",
                "position": "Desarrolladora Senior",
                "industry": "Tecnología",
                "location": "Madrid, España",
                "phone": "+34 600 123 456",
                "notes": "Especialista en React y Node.js, interesada en IA"
            },
            {
                "name": "Carlos Rodríguez",
                "email": "carlos.rodriguez@consulting.com",
                "company": "Consulting Plus",
                "position": "Consultor Senior",
                "industry": "Consultoría",
                "location": "Barcelona, España",
                "phone": "+34 600 234 567",
                "notes": "Experto en transformación digital y estrategia empresarial"
            },
            {
                "name": "Ana López",
                "email": "ana.lopez@fintech.com",
                "company": "FinTech Solutions",
                "position": "Directora de Producto",
                "industry": "Finanzas",
                "location": "Valencia, España",
                "phone": "+34 600 345 678",
                "notes": "Líder en productos financieros digitales y blockchain"
            },
            {
                "name": "David Martín",
                "email": "david.martin@healthtech.com",
                "company": "HealthTech",
                "position": "CTO",
                "industry": "Salud",
                "location": "Sevilla, España",
                "phone": "+34 600 456 789",
                "notes": "Innovador en tecnología médica y telemedicina"
            },
            {
                "name": "Laura Sánchez",
                "email": "laura.sanchez@edutech.com",
                "company": "EduTech",
                "position": "Directora de Innovación",
                "industry": "Educación",
                "location": "Bilbao, España",
                "phone": "+34 600 567 890",
                "notes": "Pionera en educación digital y e-learning"
            },
            {
                "name": "Roberto Fernández",
                "email": "roberto.fernandez@marketing.com",
                "company": "Marketing Pro",
                "position": "Director de Marketing",
                "industry": "Marketing",
                "location": "Málaga, España",
                "phone": "+34 600 678 901",
                "notes": "Especialista en marketing digital y redes sociales"
            },
            {
                "name": "Elena Ruiz",
                "email": "elena.ruiz@startup.com",
                "company": "StartupHub",
                "position": "Fundadora",
                "industry": "Tecnología",
                "location": "Madrid, España",
                "phone": "+34 600 789 012",
                "notes": "Emprendedora serial, mentora de startups"
            },
            {
                "name": "Javier Moreno",
                "email": "javier.moreno@consulting.com",
                "company": "Strategy Consulting",
                "position": "Partner",
                "industry": "Consultoría",
                "location": "Barcelona, España",
                "phone": "+34 600 890 123",
                "notes": "Consultor estratégico con 15 años de experiencia"
            },
            {
                "name": "Carmen Jiménez",
                "email": "carmen.jimenez@bank.com",
                "company": "Banco Digital",
                "position": "Directora de Innovación",
                "industry": "Finanzas",
                "location": "Valencia, España",
                "phone": "+34 600 901 234",
                "notes": "Experta en banca digital y fintech"
            },
            {
                "name": "Miguel Torres",
                "email": "miguel.torres@hospital.com",
                "company": "Hospital Universitario",
                "position": "Director de Sistemas",
                "industry": "Salud",
                "location": "Sevilla, España",
                "phone": "+34 600 012 345",
                "notes": "Especialista en sistemas hospitalarios y digitalización"
            }
        ]
        
        # Crear contactos
        created_contacts = []
        for contact_data in sample_contacts:
            contact = Contact(
                user_id=user.id,
                name=contact_data["name"],
                email=contact_data["email"],
                company=contact_data["company"],
                position=contact_data["position"],
                industry=contact_data["industry"],
                location=contact_data["location"],
                phone=contact_data.get("phone"),
                notes=contact_data.get("notes")
            )
            db.session.add(contact)
            created_contacts.append(contact)
        
        db.session.commit()
        print(f"✅ {len(created_contacts)} contactos creados")
        
        # Crear perfiles sociales de ejemplo
        social_platforms = ['LinkedIn', 'Instagram', 'TikTok', 'Facebook']
        social_profiles_created = 0
        
        for contact in created_contacts:
            # Cada contacto tendrá 1-3 perfiles sociales
            import random
            num_profiles = random.randint(1, 3)
            selected_platforms = random.sample(social_platforms, num_profiles)
            
            for platform in selected_platforms:
                profile = SocialProfile(
                    contact_id=contact.id,
                    platform=platform,
                    username=f"{contact.name.lower().replace(' ', '.')}",
                    url=f"https://{platform.lower()}.com/{contact.name.lower().replace(' ', '.')}",
                    followers=random.randint(100, 10000),
                    engagement_rate=round(random.uniform(1.0, 8.0), 2)
                )
                db.session.add(profile)
                social_profiles_created += 1
        
        db.session.commit()
        print(f"✅ {social_profiles_created} perfiles sociales creados")
        
        # Crear métricas de red iniciales
        network_metric = NetworkMetric(
            user_id=user.id,
            total_contacts=len(created_contacts),
            total_connections=0,
            network_density=0.0,
            diversity_score=len(set(c.industry for c in created_contacts)) / len(created_contacts),
            influence_score=0.0
        )
        db.session.add(network_metric)
        
        # Crear log de actividad
        activity_log = ActivityLog(
            user_id=user.id,
            action="sample_data_created",
            details=f"Datos de ejemplo creados: {len(created_contacts)} contactos, {social_profiles_created} perfiles sociales"
        )
        db.session.add(activity_log)
        
        db.session.commit()
        
        print("\n📊 Resumen de datos creados:")
        print(f"👤 Usuario: {user.username}")
        print(f"📇 Contactos: {len(created_contacts)}")
        print(f"📱 Perfiles sociales: {social_profiles_created}")
        print(f"🏢 Industrias representadas: {len(set(c.industry for c in created_contacts))}")
        print(f"🌍 Ubicaciones: {len(set(c.location for c in created_contacts))}")
        
        print("\n🎯 Datos de ejemplo creados exitosamente!")
        print("💡 Ahora puedes usar la aplicación con datos realistas para testing.")

if __name__ == "__main__":
    create_sample_data()

