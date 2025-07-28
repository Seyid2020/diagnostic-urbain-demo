import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import json
import os
from groq import Groq
import openai
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import io
import base64

# Configuration de la page
st.set_page_config(
    page_title="Smart City QuickScan",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        padding: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .recommendation-box {
        background: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .info-box {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e3c72;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_ai_clients():
    """Initialise les clients IA avec gestion d'erreurs"""
    clients = {}
    
    # Configuration Groq
    groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            clients['groq'] = Groq(api_key=groq_api_key)
        except Exception as e:
            st.warning(f"Erreur Groq: {e}")
    
    # Configuration OpenAI
    openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        try:
            openai.api_key = openai_api_key
            clients['openai'] = openai
        except Exception as e:
            st.warning(f"Erreur OpenAI: {e}")
    
    return clients

def search_web_info(query, max_results=3):
    """Recherche d'informations sur le web avec gestion d'erreurs"""
    try:
        # Simulation d'une recherche web (remplacez par une vraie API)
        search_results = [
            {
                "title": f"Résultat pour: {query}",
                "url": "https://example.com",
                "snippet": "Information trouvée sur le web..."
            }
        ]
        return search_results
    except Exception as e:
        return []

def generate_enhanced_content(prompt, clients, max_tokens=500, include_Web Search=False):
    """Génère du contenu avec les clients IA disponibles"""
    
    if include_Web Search:
        # Extraire les mots-clés pour la recherche web
        search_query = prompt.split(":")[-1].strip() if ":" in prompt else prompt
        web_results = search_web_info(search_query)
        
        if web_results:
            web_context = "\n".join([f"- {result['snippet']} (Source: {result['url']})" for result in web_results])
            prompt += f"\n\nInformations web récentes:\n{web_context}"
    
    # Essayer Groq en premier
    if 'groq' in clients:
        try:
            response = clients['groq'].chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            content = response.choices[0].message.content
            
            # Ajouter la source si recherche web
            if include_Web Search and web_results:
                content += f"\n\n📍 *Sources web consultées: {', '.join([r['url'] for r in web_results])}"
            
            return content
        except Exception as e:
            st.warning(f"Erreur Groq: {e}")
    
    # Fallback vers OpenAI
    if 'openai' in clients:
        try:
            response = clients['openai'].ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            content = response.choices[0].message.content
            
            if include_Web Search and web_results:
                content += f"\n\n📍 *Sources web consultées: {', '.join([r['url'] for r in web_results])}"
            
            return content
        except Exception as e:
            st.warning(f"Erreur OpenAI: {e}")
    
    return "❌ Aucun service IA disponible. Veuillez vérifier vos clés API."

def calculate_smart_city_score(data):
    """Calcule le score Smart City basé sur les données fournies"""
    weights = {
        'infrastructure': 0.25,
        'governance': 0.20,
        'environment': 0.20,
        'economy': 0.15,
        'social': 0.20
    }
    
    scores = {}
    
    # Infrastructure (0-100)
    infra_score = (
        (data.get('electricity_access', 0) * 0.3) +
        (data.get('water_access', 0) * 0.3) +
        (data.get('internet_penetration', 0) * 0.2) +
        (data.get('road_quality', 50) * 0.2)
    )
    scores['infrastructure'] = min(100, infra_score)
    
    # Gouvernance (0-100)
    gov_score = (
        (data.get('digital_services', 0) * 0.4) +
        (data.get('transparency_index', 50) * 0.3) +
        (data.get('citizen_participation', 30) * 0.3)
    )
    scores['governance'] = min(100, gov_score)
    
    # Environnement (0-100)
    env_score = (
        (100 - data.get('pollution_level', 50)) * 0.4 +
        (data.get('green_spaces', 20) * 0.3) +
        (data.get('waste_management', 40) * 0.3)
    )
    scores['environment'] = min(100, env_score)
    
    # Économie (0-100)
    eco_score = (
        (data.get('gdp_per_capita', 2000) / 50) +  # Normalisé
        (data.get('employment_rate', 60)) +
        (data.get('business_environment', 50))
    ) / 3
    scores['economy'] = min(100, eco_score)
    
    # Social (0-100)
    social_score = (
        (data.get('education_index', 60) * 0.4) +
        (data.get('health_index', 60) * 0.3) +
        (data.get('safety_index', 50) * 0.3)
    )
    scores['social'] = min(100, social_score)
    
    # Score global
    total_score = sum(scores[key] * weights[key] for key in weights.keys())
    
    return total_score, scores

def create_radar_chart(scores):
    """Crée un graphique radar des scores"""
    categories = ['Infrastructure', 'Gouvernance', 'Environnement', 'Économie', 'Social']
    values = [scores['infrastructure'], scores['governance'], scores['environment'], 
              scores['economy'], scores['social']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Score actuel',
        line_color='rgb(30, 60, 114)',
        fillcolor='rgba(30, 60, 114, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Profil Smart City",
        height=400
    )
    
    return fig

def create_comparison_chart(city_score, benchmarks):
    """Crée un graphique de comparaison avec d'autres villes"""
    cities = list(benchmarks.keys()) + ['Votre ville']
    scores = list(benchmarks.values()) + [city_score]
    colors_list = ['lightblue'] * len(benchmarks) + ['darkblue']
    
    fig = go.Figure(data=[
        go.Bar(x=cities, y=scores, marker_color=colors_list)
    ])
    
    fig.update_layout(
        title="Comparaison avec d'autres villes",
        xaxis_title="Villes",
        yaxis_title="Score Smart City",
        height=400
    )
    
    return fig

def generate_recommendations(scores, city_data):
    """Génère des recommandations basées sur les scores"""
    recommendations = []
    
    # Analyse des points faibles
    weak_areas = {k: v for k, v in scores.items() if v < 60}
    
    if 'infrastructure' in weak_areas:
        recommendations.append({
            'priority': 'Haute',
            'domain': 'Infrastructure',
            'action': 'Améliorer l\'accès à l\'électricité et à l\'eau potable',
            'impact': 'Fondamental pour le développement urbain'
        })
    
    if 'governance' in weak_areas:
        recommendations.append({
            'priority': 'Haute',
            'domain': 'Gouvernance',
            'action': 'Développer les services numériques municipaux',
            'impact': 'Amélioration de l\'efficacité administrative'
        })
    
    if 'environment' in weak_areas:
        recommendations.append({
            'priority': 'Moyenne',
            'domain': 'Environnement',
            'action': 'Créer plus d\'espaces verts et améliorer la gestion des déchets',
            'impact': 'Qualité de vie et durabilité'
        })
    
    return recommendations

def create_pdf_report(city_name, total_score, scores, recommendations, charts_data):
    """Génère un rapport PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3c72')
    )
    
    story.append(Paragraph(f"Diagnostic Smart City - {city_name}", title_style))
    story.append(Spacer(1, 20))
    
    # Score global
    score_style = ParagraphStyle(
        'ScoreStyle',
        parent=styles['Normal'],
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2a5298')
    )
    
    story.append(Paragraph(f"Score Global: {total_score:.1f}/100", score_style))
    story.append(Spacer(1, 20))
    
    # Scores détaillés
    story.append(Paragraph("Scores par Domaine", styles['Heading2']))
    
    score_data = [['Domaine', 'Score', 'Niveau']]
    for domain, score in scores.items():
        level = 'Excellent' if score >= 80 else 'Bon' if score >= 60 else 'À améliorer'
        score_data.append([domain.capitalize(), f"{score:.1f}", level])
    
    score_table = Table(score_data)
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # Recommandations
    story.append(Paragraph("Recommandations Prioritaires", styles['Heading2']))
    
    for i, rec in enumerate(recommendations[:5], 1):
        story.append(Paragraph(f"{i}. {rec['action']}", styles['Normal']))
        story.append(Paragraph(f"   Domaine: {rec['domain']} | Priorité: {rec['priority']}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def data_input_tab():
    """Onglet de saisie des données"""
    st.markdown('<div class="main-header">📊 SAISIE DES DONNÉES</div>', unsafe_allow_html=True)
    
    # Informations générales
    st.subheader("🏙️ Informations Générales")
    col1, col2 = st.columns(2)
    
    with col1:
        city_name = st.text_input("Nom de la ville", value="Nouakchott")
        country = st.text_input("Pays", value="Mauritanie")
        population = st.number_input("Population", min_value=1000, value=1500000, step=1000)
    
    with col2:
        area = st.number_input("Superficie (km²)", min_value=1, value=1000, step=10)
        gdp_per_capita = st.number_input("PIB par habitant (USD)", min_value=100, value=2000, step=100)
        year = st.selectbox("Année de référence", [2024, 2023, 2022, 2021], index=0)
    
    st.markdown("---")
    
    # Infrastructure
    st.subheader("🏗️ Infrastructure")
    col1, col2 = st.columns(2)
    
    with col1:
        electricity_access = st.slider("Accès à l'électricité (%)", 0, 100, 75)
        water_access = st.slider("Accès à l'eau potable (%)", 0, 100, 60)
        sanitation_access = st.slider("Accès à l'assainissement (%)", 0, 100, 40)
    
    with col2:
        internet_penetration = st.slider("Pénétration Internet (%)", 0, 100, 45)
        road_quality = st.slider("Qualité des routes (1-100)", 0, 100, 50)
        public_transport = st.slider("Couverture transport public (%)", 0, 100, 30)
    
    st.markdown("---")
    
    # Gouvernance
    st.subheader("🏛️ Gouvernance")
    col1, col2 = st.columns(2)
    
    with col1:
        digital_services = st.slider("Services numériques municipaux (%)", 0, 100, 25)
        transparency_index = st.slider("Indice de transparence", 0, 100, 50)
    
    with col2:
        citizen_participation = st.slider("Participation citoyenne (%)", 0, 100, 30)
        corruption_index = st.slider("Indice de corruption (0=très corrompu)", 0, 100, 40)
    
    st.markdown("---")
    
    # Environnement
    st.subheader("🌱 Environnement")
    col1, col2 = st.columns(2)
    
    with col1:
        air_quality = st.slider("Qualité de l'air (0=très pollué, 100=excellent)", 0, 100, 60)
        green_spaces = st.slider("Espaces verts par habitant (m²)", 0, 50, 5)
    
    with col2:
        waste_management = st.slider("Efficacité gestion des déchets (%)", 0, 100, 40)
        renewable_energy = st.slider("Part énergies renouvelables (%)", 0, 100, 10)
    
    st.markdown("---")
    
    # Social
    st.subheader("👥 Indicateurs Sociaux")
    col1, col2 = st.columns(2)
    
    with col1:
        education_index = st.slider("Indice d'éducation", 0, 100, 60)
        health_index = st.slider("Indice de santé", 0, 100, 55)
    
    with col2:
        employment_rate = st.slider("Taux d'emploi (%)", 0, 100, 45)
        safety_index = st.slider("Indice de sécurité", 0, 100, 50)
    
    # Stockage des données dans session_state
    city_data = {
        'city_name': city_name,
        'country': country,
        'population': population,
        'area': area,
        'gdp_per_capita': gdp_per_capita,
        'year': year,
        'electricity_access': electricity_access,
        'water_access': water_access,
        'sanitation_access': sanitation_access,
        'internet_penetration': internet_penetration,
        'road_quality': road_quality,
        'public_transport': public_transport,
        'digital_services': digital_services,
        'transparency_index': transparency_index,
        'citizen_participation': citizen_participation,
        'corruption_index': corruption_index,
        'air_quality': air_quality,
        'green_spaces': green_spaces,
        'waste_management': waste_management,
        'renewable_energy': renewable_energy,
        'education_index': education_index,
        'health_index': health_index,
        'employment_rate': employment_rate,
        'safety_index': safety_index
    }
    
    st.session_state.city_data = city_data
    
    if st.button("🚀 Lancer l'Analyse", type="primary", use_container_width=True):
        st.success("✅ Données enregistrées ! Consultez l'onglet 'Analyse' pour voir les résultats.")

def analysis_tab():
    """Onglet d'analyse et résultats"""
    st.markdown('<div class="main-header">📈 ANALYSE SMART CITY</div>', unsafe_allow_html=True)
    
    if 'city_data' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord saisir les données dans l'onglet 'Données'")
        return
    
    city_data = st.session_state.city_data
    
    # Calcul des scores
    total_score, scores = calculate_smart_city_score(city_data)
    
    # Affichage du score global
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        score_color = "#28a745" if total_score >= 70 else "#ffc107" if total_score >= 50 else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {score_color}20, {score_color}10); border-radius: 15px; margin: 1rem 0;">
            <h1 style="color: {score_color}; margin: 0; font-size: 3rem;">{total_score:.1f}/100</h1>
            <h3 style="color: #333; margin: 0.5rem 0;">Score Smart City Global</h3>
            <p style="color: #666; margin: 0;">{city_data['city_name']}, {city_data['country']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Métriques détaillées
    st.subheader("📊 Scores par Domaine")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = [
        ("Infrastructure", scores['infrastructure'], "🏗️"),
        ("Gouvernance", scores['governance'], "🏛️"),
        ("Environnement", scores['environment'], "🌱"),
        ("Économie", scores['economy'], "💼"),
        ("Social", scores['social'], "👥")
    ]
    
    for i, (col, (name, score, icon)) in enumerate(zip([col1, col2, col3, col4, col5], metrics)):
        with col:
            color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {color}, {color}dd);">
                <div style="font-size: 2rem;">{icon}</div>
                <div class="metric-value">{score:.1f}</div>
                <div class="metric-label">{name}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Profil Smart City")
        radar_chart = create_radar_chart(scores)
        st.plotly_chart(radar_chart, use_container_width=True)
    
    with col2:
        st.subheader("🌍 Comparaison Internationale")
        benchmarks = {
            'Singapour': 87.2,
            'Barcelone': 82.5,
            'Amsterdam': 80.1,
            'Casablanca': 58.3,
            'Le Caire': 52.7,
            'Lagos': 45.2
        }
        comparison_chart = create_comparison_chart(total_score, benchmarks)
        st.plotly_chart(comparison_chart, use_container_width=True)
    
    # Analyse détaillée avec IA
    st.markdown("---")
    st.subheader("🤖 Analyse IA Approfondie")
    
    if st.button("🚀 Générer l'Analyse IA", type="primary"):
        with st.spinner("Analyse en cours..."):
            clients = initialize_ai_clients()
            
            analysis_prompt = f"""
            Analysez ce diagnostic Smart City pour {city_data['city_name']}, {city_data['country']}:
            
            Score global: {total_score:.1f}/100
            - Infrastructure: {scores['infrastructure']:.1f}/100
            - Gouvernance: {scores['governance']:.1f}/100  
            - Environnement: {scores['environment']:.1f}/100
            - Économie: {scores['economy']:.1f}/100
            - Social: {scores['social']:.1f}/100
            
            Population: {city_data['population']:,} habitants
            PIB/hab: {city_data['gdp_per_capita']} USD
            
            Fournissez une analyse concise (max 300 mots) avec:
            1. Points forts principaux
            2. Défis majeurs  
            3. 3 recommandations prioritaires
            4. Potentiel de développement
            """
            
            analysis = generate_enhanced_content(analysis_prompt, clients, 400)
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 🎯 Analyse Experte")
            st.markdown(analysis)
            st.markdown('</div>', unsafe_allow_html=True)

def recommendations_tab():
    """Onglet des recommandations"""
    st.markdown('<div class="main-header">💡 RECOMMANDATIONS</div>', unsafe_allow_html=True)
    
    if 'city_data' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer l'analyse dans les onglets précédents")
        return
    
    city_data = st.session_state.city_data
    total_score, scores = calculate_smart_city_score(city_data)
    recommendations = generate_recommendations(scores, city_data)
    
    # Plan d'action stratégique
    st.subheader("🎯 Plan d'Action Stratégique")
    
    # Recommandations par priorité
    high_priority = [r for r in recommendations if r['priority'] == 'Haute']
    medium_priority = [r for r in recommendations if r['priority'] == 'Moyenne']
    
    if high_priority:
        st.markdown("### 🔴 Priorité Haute")
        for i, rec in enumerate(high_priority, 1):
            st.markdown(f"""
            <div class="warning-box">
                <strong>{i}. {rec['action']}</strong><br>
                <em>Domaine:</em> {rec['domain']}<br>
                <em>Impact:</em> {rec['impact']}
            </div>
            """, unsafe_allow_html=True)
    
    if medium_priority:
        st.markdown("### 🟡 Priorité Moyenne")
        for i, rec in enumerate(medium_priority, 1):
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>{i}. {rec['action']}</strong><br>
                <em>Domaine:</em> {rec['domain']}<br>
                <em>Impact:</em> {rec['impact']}
            </div>
            """, unsafe_allow_html=True)
    
    # Recommandations IA personnalisées
    st.markdown("---")
    st.subheader("🤖 Recommandations IA Personnalisées")
    
    if st.button("🚀 Générer Recommandations Détaillées", type="primary"):
        with st.spinner("Génération des recommandations..."):
            clients = initialize_ai_clients()
            
            rec_prompt = f"""
            Générez des recommandations détaillées pour améliorer le score Smart City de {city_data['city_name']}, {city_data['country']}.
            
            Situation actuelle:
            - Score global: {total_score:.1f}/100
            - Points faibles: {[k for k, v in scores.items() if v < 60]}
            - Population: {city_data['population']:,}
            - Contexte: Ville africaine en développement
            
            Fournissez:
            1. 5 actions concrètes et réalisables
            2. Estimation des coûts (faible/moyen/élevé)
            3. Délais de mise en œuvre
            4. Partenaires potentiels
            5. Indicateurs de suivi
            
            Format: Actions numérotées, concises et pratiques.
            """
            
            detailed_recs = generate_enhanced_content(rec_prompt, clients, 600)
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 📋 Plan d'Action Détaillé")
            st.markdown(detailed_recs)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Simulation d'impact
    st.markdown("---")
    st.subheader("📊 Simulation d'Impact")
    
    st.markdown("Estimez l'impact potentiel des améliorations:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Améliorations Infrastructure:**")
        infra_improvement = st.slider("Amélioration Infrastructure (%)", 0, 50, 20)
        
        st.markdown("**Améliorations Gouvernance:**")
        gov_improvement = st.slider("Amélioration Gouvernance (%)", 0, 50, 15)
    
    with col2:
        st.markdown("**Améliorations Environnement:**")
        env_improvement = st.slider("Amélioration Environnement (%)", 0, 50, 25)
        
        st.markdown("**Améliorations Social:**")
        social_improvement = st.slider("Amélioration Social (%)", 0, 50, 20)
    
    # Calcul du nouveau score
    new_scores = scores.copy()
    new_scores['infrastructure'] = min(100, scores['infrastructure'] + infra_improvement)
    new_scores['governance'] = min(100, scores['governance'] + gov_improvement)
    new_scores['environment'] = min(100, scores['environment'] + env_improvement)
    new_scores['social'] = min(100, scores['social'] + social_improvement)
    
    weights = {'infrastructure': 0.25, 'governance': 0.20, 'environment': 0.20, 'economy': 0.15, 'social': 0.20}
    new_total_score = sum(new_scores[key] * weights[key] for key in weights.keys())
    
    improvement = new_total_score - total_score
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score Actuel", f"{total_score:.1f}", "")
    with col2:
        st.metric("Score Projeté", f"{new_total_score:.1f}", f"+{improvement:.1f}")
    with col3:
        improvement_pct = (improvement / total_score) * 100
        st.metric("Amélioration", f"{improvement_pct:.1f}%", "")

def report_tab():
    """Onglet de génération de rapport"""
    st.markdown('<div class="main-header">📄 RAPPORT FINAL</div>', unsafe_allow_html=True)
    
    if 'city_data' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer l'analyse complète")
        return
    
    city_data = st.session_state.city_data
    total_score, scores = calculate_smart_city_score(city_data)
    recommendations = generate_recommendations(scores, city_data)
    
    # Aperçu du rapport
    st.subheader("📋 Aperçu du Rapport")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **Ville:** {city_data['city_name']}, {city_data['country']}  
        **Population:** {city_data['population']:,} habitants  
        **Score Smart City:** {total_score:.1f}/100  
        **Date d'analyse:** {datetime.now().strftime('%d/%m/%Y')}
        
        **Contenu du rapport:**
        - ✅ Résumé exécutif
        - ✅ Scores détaillés par domaine  
        - ✅ Analyse comparative internationale
        - ✅ Recommandations prioritaires
        - ✅ Plan d'action stratégique
        - ✅ Indicateurs de suivi
        """)
    
    with col2:
        # Génération du PDF
        if st.button("📥 Télécharger PDF", type="primary", use_container_width=True):
            with st.spinner("Génération du rapport PDF..."):
                pdf_buffer = create_pdf_report(
                    city_data['city_name'], 
                    total_score, 
                    scores, 
                    recommendations,
                    {}
                )
                
                st.download_button(
                    label="💾 Télécharger le Rapport PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"Smart_City_Report_{city_data['city_name']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        # Export des données
        if st.button("📊 Exporter Données", use_container_width=True):
            export_data = {
                'ville': city_data['city_name'],
                'pays': city_data['country'],
                'score_global': total_score,
                **scores,
                'date_analyse': datetime.now().isoformat()
            }
            
            df = pd.DataFrame([export_data])
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="💾 Télécharger CSV",
                data=csv,
                file_name=f"smart_city_data_{city_data['city_name']}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Rapport détaillé avec IA
    st.markdown("---")
    st.subheader("🤖 Rapport Exécutif IA")
    
    if st.button("📝 Générer Rapport Exécutif", type="primary"):
        with st.spinner("Rédaction du rapport exécutif..."):
            clients = initialize_ai_clients()
            
            executive_prompt = f"""
            Rédigez un rapport exécutif professionnel pour le diagnostic Smart City de {city_data['city_name']}, {city_data['country']}.
            
            DONNÉES CLÉS:
            - Score global: {total_score:.1f}/100
            - Infrastructure: {scores['infrastructure']:.1f}/100
            - Gouvernance: {scores['governance']:.1f}/100
            - Environnement: {scores['environment']:.1f}/100
            - Économie: {scores['economy']:.1f}/100
            - Social: {scores['social']:.1f}/100
            - Population: {city_data['population']:,} habitants
            
            STRUCTURE REQUISE:
            1. RÉSUMÉ EXÉCUTIF (2-3 phrases)
            2. SITUATION ACTUELLE (forces/faiblesses)
            3. ENJEUX PRIORITAIRES (3 points max)
            4. RECOMMANDATIONS STRATÉGIQUES (3 actions)
            5. IMPACT ATTENDU
            
            Style: Professionnel, concis, orienté décision. Max 400 mots.
            """
            
            executive_report = generate_enhanced_content(executive_prompt, clients, 500)
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 📊 Rapport Exécutif")
            st.markdown(executive_report)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sauvegarder le rapport
            st.session_state.executive_report = executive_report

def chatbot_tab():
    """Onglet Chatbot pour assistance IA"""
    st.markdown('<div class="main-header">🤖 ASSISTANT IA URBAIN</div>', unsafe_allow_html=True)
    
    # Initialisation des clients IA
    clients = initialize_ai_clients()
    
    # Interface du chatbot
    st.markdown("""
    ### 💬 Posez vos questions sur le développement urbain
    
    Cet assistant IA peut vous aider avec :
    - **Analyse de données urbaines** 📊
    - **Recommandations de politiques** 🏛️
    - **Comparaisons entre villes** 🌍
    - **Interprétation d'indicateurs** 📈
    - **Stratégies de développement** 🚀
    """)
    
    # Historique des conversations
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Bonjour ! Je suis votre assistant IA spécialisé en développement urbain. Comment puis-je vous aider aujourd'hui ?"
            }
        ]
    
    # Affichage des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Zone de saisie
    if prompt := st.chat_input("Tapez votre question ici..."):
        # Ajout du message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Génération de la réponse
        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours..."):
                
                # Contexte spécialisé pour l'urbanisme
                system_prompt = """
                Vous êtes un expert en développement urbain et planification urbaine, spécialisé dans les villes africaines.
                Vous aidez les urbanistes, décideurs et chercheurs avec des analyses précises et des recommandations pratiques.
                
                RÈGLES IMPORTANTES:
                - Répondez UNIQUEMENT aux questions liées à l'urbanisme et au développement urbain
                - Si vous ne connaissez pas une information précise, dites "Je ne connais pas cette information spécifique"
                - Si vous trouvez des informations sur le web, indiquez clairement la source
                - Gardez vos réponses courtes et précises (max 150 mots)
                - Concentrez-vous sur les villes africaines quand c'est pertinent
                
                Vos domaines d'expertise incluent :
                - Planification urbaine et aménagement du territoire
                - Infrastructures urbaines (eau, électricité, transport, assainissement)
                - Habitat et logement social
                - Économie urbaine et développement local
                - Gouvernance urbaine et participation citoyenne
                - Résilience climatique et développement durable
                - Démographie urbaine et migration
                - Services urbains de base
                """
                
                # Vérifier si la question est liée à l'urbanisme
                urban_keywords = ['ville', 'urbain', 'infrastructure', 'transport', 'logement', 'eau', 'électricité', 
                                'gouvernance', 'planification', 'développement', 'population', 'habitat', 'assainissement',
                                'smart city', 'municipalité', 'maire', 'conseil', 'citoyen', 'service public']
                
                is_urban_related = any(keyword in prompt.lower() for keyword in urban_keywords)
                
                if not is_urban_related:
                    response = "Je suis spécialisé uniquement dans les questions de développement urbain et de planification urbaine. Pouvez-vous reformuler votre question en lien avec ces domaines ?"
                else:
                    # Recherche web si nécessaire
                    needs_Web Search = any(word in prompt.lower() for word in ['récent', 'dernier', 'nouveau', 'actuel', '2024', '2025'])
                    
                    full_prompt = f"""
                    {system_prompt}
                    
                    Question de l'utilisateur : {prompt}
                    
                    Contexte : Nous travaillons sur un diagnostic urbain pour des villes africaines, notamment Nouakchott en Mauritanie.
                    
                    Répondez de manière concise et pratique. Si vous ne connaissez pas une information précise, dites-le clairement.
                    """
                    
                    response = generate_enhanced_content(full_prompt, clients, 200, include_Web Search=needs_Web Search)
                
                st.markdown(response)
                
                # Ajout de la réponse à l'historique
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Suggestions de questions
    st.markdown("---")
    st.markdown("### 💡 Questions suggérées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Comment améliorer l'accès au logement décent ?"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment améliorer l'accès au logement décent ?"
            })
            st.rerun()
        
        if st.button("💧 Stratégies pour l'accès à l'eau potable"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Quelles sont les meilleures stratégies pour améliorer l'accès à l'eau potable en milieu urbain africain ?"
            })
            st.rerun()
        
        if st.button("🚌 Développer le transport public"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment développer un système de transport public efficace dans une ville en croissance rapide ?"
            })
            st.rerun()
    
    with col2:
        if st.button("📊 Interpréter les indicateurs urbains"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment interpréter et utiliser les indicateurs urbains pour la prise de décision ?"
            })
            st.rerun()
        
        if st.button("🌱 Résilience climatique urbaine"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Quelles mesures prendre pour renforcer la résilience climatique d'une ville sahélienne ?"
            })
            st.rerun()
        
        if st.button("💼 Créer des emplois urbains"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Quelles stratégies pour créer des emplois durables en milieu urbain africain ?"
            })
            st.rerun()
    
    # Bouton pour effacer l'historique
    if st.button("🗑️ Effacer la conversation", type="secondary"):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Bonjour ! Je suis votre assistant IA spécialisé en développement urbain. Comment puis-je vous aider aujourd'hui ?"
            }
        ]
        st.rerun()

def main():
    """Fonction principale de l'application"""
    
    # Sidebar avec informations
    with st.sidebar:
        st.markdown("### 🏙️ Smart City QuickScan")
        st.markdown("---")
        st.markdown("""
        **Outil de diagnostic urbain intelligent**
        
        📊 **Fonctionnalités:**
        - Évaluation multi-critères
        - Benchmarking international  
        - Recommandations IA
        - Rapports personnalisés
        - Assistant IA urbain
        
        🎯 **Objectif:**
        Évaluer le potentiel Smart City des villes africaines en 5 minutes
        """)
        
        st.markdown("---")
        st.markdown("**Développé par:** African Cities Lab")
        st.markdown("**Version:** 2.0")
    
    # Navigation par onglets
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Données", 
        "📈 Analyse", 
        "💡 Recommandations", 
        "📄 Rapport",
        "🤖 Chatbot"
    ])
    
    with tab1:
        data_input_tab()
    
    with tab2:
        analysis_tab()
    
    with tab3:
        recommendations_tab()
    
    with tab4:
        report_tab()
        
    with tab5:
        chatbot_tab()

if __name__ == "__main__":
    main()
