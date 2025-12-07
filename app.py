import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openai
from groq import Groq
import requests
import json
import PyPDF2
import io
from PIL import Image
import pytesseract
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import base64
import wikipedia
import os

# Configuration de la page
st.set_page_config(
    page_title="AfricanCities IA Services",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS amélioré
st.markdown("""
<style>
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 2px;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #f0f8ff;
        margin-bottom: 1rem;
        font-style: italic;
        font-weight: 300;
    }
    
    .institution {
        font-size: 1rem;
        color: #e6f3ff;
        font-weight: 500;
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background: rgba(255,255,255,0.1);
        border-radius: 25px;
        display: inline-block;
        backdrop-filter: blur(10px);
    }
    
    .logo-container {
        margin-bottom: 1rem;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-left: 4px solid #2c5aa0;
        border-radius: 5px;
    }
    
    .subsection-header {
        font-size: 1.4rem;
        font-weight: bold;
        color: #34495e;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        padding: 0.3rem;
        border-bottom: 2px solid #bdc3c7;
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e1e8ed;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .score-value {
        font-size: 3.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    .professional-text {
        text-align: justify;
        line-height: 1.8;
        color: #2c3e50;
        font-size: 1.05rem;
        padding: 1rem;
        background-color: #f9f9f9;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .form-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    
    .scenario-box {
        background-color: #e8f4fd;
        border: 2px solid #17a2b8;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .comparison-table {
        width: 100%;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    """Convertit une image en base64"""
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

import streamlit as st
import base64
import os

import streamlit as st
from PIL import Image
import os

def create_header():
    """Crée le header avec logo et titres"""
    logo_path = "logo-cus.png"
    
    # Afficher le logo directement avec Streamlit (pas en HTML)
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=200)
    
    # Le reste en HTML
    st.markdown("""
    <div class="header-container">
        <div class="main-title">AfricanCities IA Services</div>
        <div class="subtitle">Diagnostiquer, comprendre, transformer votre ville</div>
        <div class="institution">Centre of Urban Systems - UM6P</div>
    </div>
    """, unsafe_allow_html=True)

def initialize_ai_clients():
    """Initialise les clients IA"""
    clients = {}
    
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            clients['openai'] = True
    except:
        pass
    
    try:
        if st.secrets.get("GROQ_API_KEY"):
            clients['groq'] = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        pass
    
    return clients

def compute_scores(
    water_access, electricity_access, sanitation_access, internet_access, road_quality,
    housing_deficit, informal_settlements, housing_cost,
    unemployment_rate, informal_economy, gdp_per_capita,
    literacy_rate, infant_mortality, life_expectancy,
    green_spaces, air_quality, waste_management,
    public_transport, traffic_congestion,
    youth_percentage, density, population
):
    """
    Calcul des scores par dimension sur 1000 points
    """
    
    # Helpers qualitatifs → score
    quality_map = {
        "Très mauvaise": 200,
        "Mauvaise": 350,
        "Moyenne": 550,
        "Bonne": 750,
        "Très bonne": 900
    }
    transport_map = {
        "Inexistant": 150,
        "Très limité": 300,
        "Limité": 500,
        "Développé": 700,
        "Très développé": 850
    }
    congestion_map = {
        "Très faible": 800,
        "Faible": 700,
        "Modérée": 550,
        "Forte": 350,
        "Très forte": 200
    }
    
    # 1) Infrastructures (sur 1000)
    infra_scores = [
        water_access * 10,
        electricity_access * 10,
        sanitation_access * 10,
        internet_access * 10,
        quality_map.get(road_quality, 500)
    ]
    infra_score = np.mean(infra_scores)
    
    # 2) Habitat (sur 1000)
    habitat_raw = 1000 - (housing_deficit / 200) - (informal_settlements * 4) - (housing_cost / 10)
    habitat_score = np.clip(habitat_raw, 0, 1000)
    
    # 3) Économie (sur 1000)
    econ_raw = 1000 - (unemployment_rate * 6) - (informal_economy * 3) + (gdp_per_capita / 10)
    econ_score = np.clip(econ_raw, 0, 1000)
    
    # 4) Social (sur 1000)
    social_raw = (literacy_rate * 4) + (1000 - infant_mortality * 10) * 0.3 + (life_expectancy / 90) * 300
    social_score = np.clip(social_raw, 0, 1000)
    
    # 5) Environnement (sur 1000)
    env_raw = (green_spaces * 20) + (quality_map.get(air_quality, 500) - 500) * 0.6 + (quality_map.get(waste_management, 500) - 500) * 0.6
    env_score = np.clip(env_raw, 0, 1000)
    
    # 6) Mobilité (sur 1000)
    mobility_raw = (transport_map.get(public_transport, 500) * 0.6) + (congestion_map.get(traffic_congestion, 500) * 0.4)
    mobility_score = np.clip(mobility_raw, 0, 1000)
    
    # 7) Démographie (sur 1000)
    demo_raw = 600 + (youth_percentage - 50) * 3 - (density / 50)
    demo_score = np.clip(demo_raw, 0, 1000)
    
    # Score global
    dimensions = {
        "Démographie": demo_score,
        "Infrastructures": infra_score,
        "Habitat": habitat_score,
        "Économie": econ_score,
        "Social": social_score,
        "Environnement": env_score,
        "Mobilité": mobility_score
    }
    score_global = float(np.mean(list(dimensions.values())))
    
    # Top forces / vulnérabilités
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
    top_forces = sorted_dims[:3]
    top_weaknesses = sorted_dims[-3:]
    
    return {
        "score_global": round(score_global, 1),
        "dimensions": {k: round(v, 1) for k, v in dimensions.items()},
        "top_forces": top_forces,
        "top_weaknesses": top_weaknesses
    }

def create_radar_chart(dim_scores):
    """Crée un graphique radar des scores par dimension"""
    categories = list(dim_scores.keys())
    values = list(dim_scores.values())
    categories += [categories[0]]
    values += [values[0]]
    
    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Score par dimension',
                line=dict(color='#667eea', width=3),
                fillcolor='rgba(102, 126, 234, 0.3)'
            )
        ]
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1000],
                tickfont=dict(size=12)
            )
        ),
        showlegend=False,
        height=500,
        title={
            'text': "Profil global de la ville (scores sur 1000)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#1f4e79'}
        }
    )
    return fig

def create_comparison_chart(current_scores, benchmark_scores):
    """Crée un graphique de comparaison avec benchmark"""
    categories = list(current_scores.keys())
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Ville actuelle',
        x=categories,
        y=list(current_scores.values()),
        marker_color='#667eea',
        text=[f"{v:.0f}" for v in current_scores.values()],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Benchmark régional',
        x=categories,
        y=list(benchmark_scores.values()),
        marker_color='#f39c12',
        text=[f"{v:.0f}" for v in benchmark_scores.values()],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparaison avec le benchmark régional (scores sur 1000)',
        xaxis_title='Dimensions',
        yaxis_title='Score',
        barmode='group',
        height=500,
        yaxis=dict(range=[0, 1000])
    )
    
    return fig

def create_demographic_evolution_chart(population, growth_rate):
    """Crée un graphique d'évolution démographique"""
    years = list(range(2020, 2036))
    populations = [population * ((1 + growth_rate/100) ** (year - 2025)) for year in years]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=populations,
        mode='lines+markers',
        name='Population projetée',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Projection démographique (taux de croissance: {growth_rate}%)',
        xaxis_title='Année',
        yaxis_title='Population',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_infrastructure_dashboard(water, electricity, sanitation, internet):
    """Crée un dashboard des infrastructures"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Eau potable', 'Électricité', 'Assainissement', 'Internet'),
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]]
    )
    
    # Eau
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=water,
        title={'text': "Accès (%)"},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "#3498db"},
               'steps': [
                   {'range': [0, 50], 'color': "#e74c3c"},
                   {'range': [50, 75], 'color': "#f39c12"},
                   {'range': [75, 100], 'color': "#2ecc71"}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}}
    ), row=1, col=1)
    
    # Électricité
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=electricity,
        title={'text': "Accès (%)"},
        delta={'reference': 75, 'increasing': {'color': "green"}},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "#f39c12"},
               'steps': [
                   {'range': [0, 50], 'color': "#e74c3c"},
                   {'range': [50, 75], 'color': "#f39c12"},
                   {'range': [75, 100], 'color': "#2ecc71"}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 75}}
    ), row=1, col=2)
    
    # Assainissement
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=sanitation,
        title={'text': "Accès (%)"},
        delta={'reference': 60, 'increasing': {'color': "green"}},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "#9b59b6"},
               'steps': [
                   {'range': [0, 50], 'color': "#e74c3c"},
                   {'range': [50, 75], 'color': "#f39c12"},
                   {'range': [75, 100], 'color': "#2ecc71"}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 60}}
    ), row=2, col=1)
    
    # Internet
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=internet,
        title={'text': "Accès (%)"},
        delta={'reference': 50, 'increasing': {'color': "green"}},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "#1abc9c"},
               'steps': [
                   {'range': [0, 50], 'color': "#e74c3c"},
                   {'range': [50, 75], 'color': "#f39c12"},
                   {'range': [75, 100], 'color': "#2ecc71"}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}}
    ), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=False, title_text="Dashboard des Infrastructures de Base")
    
    return fig

def calculate_scenario_costs(scenario_type, population, current_value, target_value):
    """Calcule les coûts d'un scénario en euros"""
    
    # Taux de change fictif USD -> EUR
    usd_to_eur = 0.92
    
    if scenario_type == "eau":
        # Coût par habitant pour améliorer l'accès à l'eau
        population_cible = int(population * (target_value - current_value) / 100)
        cout_par_hab_usd = 120  # USD
        cout_total_usd = population_cible * cout_par_hab_usd
        cout_total_eur = cout_total_usd * usd_to_eur
        
        benefices_sante = population_cible * 0.15  # 15% réduction maladies hydriques
        benefices_economiques = population_cible * 50 * usd_to_eur  # 50 USD/an/hab en gains économiques
        
        return {
            "population_cible": population_cible,
            "cout_total_eur": cout_total_eur,
            "cout_par_hab_eur": cout_par_hab_usd * usd_to_eur,
            "benefices_sante": int(benefices_sante),
            "benefices_economiques_annuels": benefices_economiques,
            "retour_investissement_ans": round(cout_total_eur / benefices_economiques, 1) if benefices_economiques > 0 else 0
        }
    
    elif scenario_type == "electricite":
        population_cible = int(population * (target_value - current_value) / 100)
        cout_par_hab_usd = 200
        cout_total_usd = population_cible * cout_par_hab_usd
        cout_total_eur = cout_total_usd * usd_to_eur
        
        benefices_economiques = population_cible * 80 * usd_to_eur
        creation_emplois = int(population_cible * 0.02)
        
        return {
            "population_cible": population_cible,
            "cout_total_eur": cout_total_eur,
            "cout_par_hab_eur": cout_par_hab_usd * usd_to_eur,
            "creation_emplois": creation_emplois,
            "benefices_economiques_annuels": benefices_economiques,
            "retour_investissement_ans": round(cout_total_eur / benefices_economiques, 1) if benefices_economiques > 0 else 0
        }
    
    elif scenario_type == "logement":
        nb_logements = int((target_value - current_value) * 1000)  # Réduction du déficit
        cout_par_logement_usd = 15000
        cout_total_usd = nb_logements * cout_par_logement_usd
        cout_total_eur = cout_total_usd * usd_to_eur
        
        population_beneficiaire = nb_logements * 5  # 5 personnes par logement
        benefices_sociaux = population_beneficiaire * 30 * usd_to_eur
        
        return {
            "nb_logements": nb_logements,
            "population_beneficiaire": population_beneficiaire,
            "cout_total_eur": cout_total_eur,
            "cout_par_logement_eur": cout_par_logement_usd * usd_to_eur,
            "benefices_sociaux_annuels": benefices_sociaux,
            "retour_investissement_ans": round(cout_total_eur / benefices_sociaux, 1) if benefices_sociaux > 0 else 0
        }
    
    elif scenario_type == "education":
        population_cible = int(population * (target_value - current_value) / 100)
        cout_par_personne_usd = 300
        cout_total_usd = population_cible * cout_par_personne_usd
        cout_total_eur = cout_total_usd * usd_to_eur
        
        benefices_economiques = population_cible * 100 * usd_to_eur
        
        return {
            "population_cible": population_cible,
            "cout_total_eur": cout_total_eur,
            "cout_par_personne_eur": cout_par_personne_usd * usd_to_eur,
            "benefices_economiques_annuels": benefices_economiques,
            "retour_investissement_ans": round(cout_total_eur / benefices_economiques, 1) if benefices_economiques > 0 else 0
        }
    
    return {}

def generate_enhanced_content(prompt, clients, max_tokens=800):
    """Génère du contenu avec IA"""
    try:
        if 'groq' in clients:
            response = clients['groq'].chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Rédigez du contenu professionnel, détaillé et précis sans emojis. Gardez vos réponses courtes et précises (max 150 mots pour le chatbot)."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        elif 'openai' in clients:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Rédigez du contenu professionnel, détaillé et précis sans emojis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        else:
            return "Service IA temporairement indisponible. Veuillez configurer vos clés API."
            
    except Exception as e:
        return f"Analyse en cours... (Service IA en configuration)"

def generate_professional_pdf_report(city_name, country, report_data):
    """Génère un rapport PDF professionnel"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1f4e79')
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#2c5aa0')
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    story = []
    
    # Page de titre
    story.append(Paragraph(f"DIAGNOSTIC URBAIN INTELLIGENT", title_style))
    story.append(Paragraph(f"Ville de {city_name}, {country}", title_style))
    story.append(Spacer(1, 50))
    story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", body_style))
    story.append(Paragraph("AfricanCities IA Services - Centre of Urban Systems UM6P", body_style))
    story.append(PageBreak())
    
    # Contenu
    story.append(Paragraph("RÉSUMÉ EXÉCUTIF", section_style))
    story.append(Paragraph(report_data.get('executive_summary', 'Contenu en génération...'), body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("SCORES ET DIAGNOSTIC", section_style))
    story.append(Paragraph(f"Score global: {report_data.get('score_global', 'N/A')}/1000", body_style))
    story.append(Spacer(1, 20))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def coach_urbain_tab():
    """Onglet Coach Urbain (ancien Chatbot)"""
    st.markdown('<div class="main-header">🎓 COACH URBAIN IA</div>', unsafe_allow_html=True)
    
    clients = initialize_ai_clients()
    
    st.markdown("""
    ### 💬 Votre assistant expert en développement urbain
    
    Le Coach Urbain peut vous aider avec :
    - **Analyse de données urbaines** 📊
    - **Recommandations de politiques** 🏛️
    - **Comparaisons entre villes** 🌍
    - **Interprétation d'indicateurs** 📈
    - **Stratégies de développement** 🚀
    """)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Bonjour ! Je suis votre Coach Urbain IA, spécialisé en développement urbain africain. Comment puis-je vous accompagner aujourd'hui ?"
            }
        ]
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Posez votre question ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                system_prompt = """
                Vous êtes un Coach Urbain expert en développement urbain et planification urbaine, spécialisé dans les villes africaines.
                Vous aidez les urbanistes, décideurs et chercheurs avec des analyses précises et des recommandations pratiques.
                
                RÈGLES:
                - Répondez UNIQUEMENT aux questions liées à l'urbanisme
                - Soyez concis (max 150 mots)
                - Concentrez-vous sur les villes africaines
                - Style professionnel et pédagogique
                """
                
                urban_keywords = ['ville', 'urbain', 'infrastructure', 'transport', 'logement', 'eau', 'électricité', 
                                'gouvernance', 'planification', 'développement', 'population', 'habitat']
                
                is_urban_related = any(keyword in prompt.lower() for keyword in urban_keywords)
                
                if not is_urban_related:
                    response = "Je suis spécialisé dans les questions de développement urbain. Pouvez-vous reformuler votre question en lien avec l'urbanisme ?"
                else:
                    full_prompt = f"{system_prompt}\n\nQuestion: {prompt}\n\nContexte: Diagnostic urbain pour villes africaines."
                    response = generate_enhanced_content(full_prompt, clients, 200)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.markdown("---")
    st.markdown("### 💡 Questions suggérées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Améliorer l'accès au logement"):
            st.session_state.messages.append({"role": "user", "content": "Comment améliorer l'accès au logement décent ?"})
            st.rerun()
        
        if st.button("💧 Stratégies pour l'eau potable"):
            st.session_state.messages.append({"role": "user", "content": "Quelles stratégies pour améliorer l'accès à l'eau potable ?"})
            st.rerun()
    
    with col2:
        if st.button("🚌 Développer le transport public"):
            st.session_state.messages.append({"role": "user", "content": "Comment développer un système de transport public efficace ?"})
            st.rerun()
        
        if st.button("🌱 Résilience climatique"):
            st.session_state.messages.append({"role": "user", "content": "Quelles mesures pour renforcer la résilience climatique urbaine ?"})
            st.rerun()
    
    if st.button("🗑️ Nouvelle conversation", type="secondary"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Bonjour ! Je suis votre Coach Urbain IA. Comment puis-je vous aider ?"}
        ]
        st.rerun()

def diagnostic_tab():
    """Onglet Diagnostic principal"""
    st.markdown('<div class="main-header">🏙️ DIAGNOSTIC URBAIN INTELLIGENT</div>', unsafe_allow_html=True)
    
    clients = initialize_ai_clients()
    
    with st.sidebar:
        st.header("⚙️ Configuration du Diagnostic")
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🌍 Informations Générales")
        city_name = st.text_input("Nom de la ville", value="Nouakchott")
        country = st.text_input("Pays", value="Mauritanie")
        region = st.text_input("Région/Province", value="Nouakchott")
        diagnostic_date = st.date_input("Date du diagnostic", value=datetime.now())
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("👥 Données Démographiques")
        population = st.number_input("Population totale (habitants)", value=1200000, step=10000)
        growth_rate = st.number_input("Taux de croissance annuel (%)", value=3.5, step=0.1)
        urban_area = st.number_input("Superficie urbaine (km²)", value=1000, step=10)
        density = st.number_input("Densité urbaine (hab/km²)", value=int(population/urban_area), step=100)
        youth_percentage = st.slider("Pourcentage de jeunes (0-25 ans) (%)", 0, 100, 60)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🏗️ Infrastructures de Base")
        water_access = st.slider("Accès à l'eau potable (%)", 0, 100, 45)
        electricity_access = st.slider("Accès à l'électricité (%)", 0, 100, 42)
        sanitation_access = st.slider("Accès à l'assainissement (%)", 0, 100, 25)
        road_quality = st.selectbox("Qualité du réseau routier", ["Très mauvaise", "Mauvaise", "Moyenne", "Bonne", "Très bonne"])
        internet_access = st.slider("Accès à Internet (%)", 0, 100, 35)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🏠 Logement et Habitat")
        housing_deficit = st.number_input("Déficit en logements", value=50000, step=1000)
        informal_settlements = st.slider("Population en habitat informel (%)", 0, 100, 40)
        housing_cost = st.number_input("Coût moyen du logement (USD/m²)", value=200, step=10)
        construction_materials = st.multiselect(
            "Matériaux de construction dominants",
            ["Béton", "Brique", "Terre", "Tôle", "Bois", "Autres"],
            default=["Béton", "Tôle"]
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("💼 Économie et Emploi")
        unemployment_rate = st.slider("Taux de chômage (%)", 0, 100, 25)
        informal_economy = st.slider("Économie informelle (%)", 0, 100, 70)
        main_sectors = st.multiselect(
            "Secteurs économiques principaux",
            ["Agriculture", "Pêche", "Commerce", "Services", "Industrie", "Tourisme", "Mines", "Autres"],
            default=["Commerce", "Services", "Pêche"]
        )
        gdp_per_capita = st.number_input("PIB par habitant (USD)", value=1500, step=100)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🏥 Services Sociaux")
        health_facilities = st.number_input("Nombre d'établissements de santé", value=15, step=1)
        schools = st.number_input("Nombre d'écoles", value=120, step=5)
        literacy_rate = st.slider("Taux d'alphabétisation (%)", 0, 100, 65)
        infant_mortality = st.number_input("Mortalité infantile (pour 1000)", value=45, step=1)
        life_expectancy = st.number_input("Espérance de vie (années)", value=65, step=1)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🌱 Environnement et Climat")
        climate_risks = st.multiselect(
            "Risques climatiques principaux",
            ["Inondations", "Sécheresse", "Érosion côtière", "Tempêtes de sable", "Canicules", "Autres"],
            default=["Inondations", "Sécheresse"]
        )
        waste_management = st.selectbox("Gestion des déchets", ["Très mauvaise", "Mauvaise", "Moyenne", "Bonne", "Très bonne"])
        green_spaces = st.slider("Espaces verts par habitant (m²)", 0, 50, 5)
        air_quality = st.selectbox("Qualité de l'air", ["Très mauvaise", "Mauvaise", "Moyenne", "Bonne", "Très bonne"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🚌 Transport et Mobilité")
        public_transport = st.selectbox("Transport public", ["Inexistant", "Très limité", "Limité", "Développé", "Très développé"])
        vehicle_ownership = st.slider("Taux de motorisation (véhicules/1000 hab)", 0, 500, 80)
        traffic_congestion = st.selectbox("Congestion routière", ["Très faible", "Faible", "Modérée", "Forte", "Très forte"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("📄 Documents Techniques")
        uploaded_files = st.file_uploader(
            "Télécharger des documents (PDF)",
            type=['pdf'],
            accept_multiple_files=True,
            help="Plans d'urbanisme, études, rapports, etc."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🎯 Type et Objectif du Diagnostic")
        diagnostic_type = st.selectbox(
            "Type de diagnostic",
            ["Diagnostic général", "Diagnostic thématique - Logement", "Diagnostic thématique - Transport", 
             "Diagnostic thématique - Environnement", "Diagnostic thématique - Économie", "Diagnostic thématique - Social"]
        )
        
        diagnostic_objective = st.text_area(
            "Objectif spécifique du diagnostic",
            value="Évaluer l'état actuel du développement urbain et identifier les priorités d'intervention pour améliorer les conditions de vie des habitants.",
            height=100
        )
        
        target_audience = st.multiselect(
            "Public cible du rapport",
            ["Autorités locales", "Gouvernement national", "Bailleurs de fonds", "ONG", "Secteur privé", "Citoyens", "Chercheurs"],
            default=["Autorités locales", "Bailleurs de fonds"]
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("💭 Commentaires et Observations")
        additional_comments = st.text_area(
            "Commentaires libres, contexte particulier, défis spécifiques...",
            height=120,
            placeholder="Décrivez ici tout élément de contexte important, défis particuliers, projets en cours, etc."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        generate_report = st.button("🚀 Générer le rapport complet", type="primary", use_container_width=True)
    
    if generate_report:
        with st.spinner("🔄 Génération du diagnostic en cours..."):
            
            # Calcul des scores
            scores = compute_scores(
                water_access, electricity_access, sanitation_access, internet_access, road_quality,
                housing_deficit, informal_settlements, housing_cost,
                unemployment_rate, informal_economy, gdp_per_capita,
                literacy_rate, infant_mortality, life_expectancy,
                green_spaces, air_quality, waste_management,
                public_transport, traffic_congestion,
                youth_percentage, density, population
            )
            
            # Benchmark fictif pour comparaison
            benchmark_scores = {
                "Démographie": 650,
                "Infrastructures": 580,
                "Habitat": 520,
                "Économie": 600,
                "Social": 550,
                "Environnement": 480,
                "Mobilité": 450
            }
            
            # === SECTION 1: SCORE GLOBAL ===
            st.markdown('<div class="section-header">🏅 SCORE GLOBAL ET SYNTHÈSE</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.markdown(f"""
                <div class="score-card">
                    <h3>Score Global</h3>
                    <div class="score-value">{scores['score_global']:.0f}</div>
                    <p style="font-size: 1.2rem;">sur 1000 points</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**🌟 Top 3 Forces:**")
                for name, val in scores["top_forces"]:
                    st.success(f"✓ {name}: {val:.0f}/1000")
                
                st.markdown("**⚠️ Top 3 Vulnérabilités:**")
                for name, val in scores["top_weaknesses"]:
                    st.error(f"✗ {name}: {val:.0f}/1000")
            
            with col2:
                radar_fig = create_radar_chart(scores["dimensions"])
                st.plotly_chart(radar_fig, use_container_width=True)
            
            with col3:
                st.markdown("### 📊 Scores par dimension")
                for dim, score in scores["dimensions"].items():
                    st.metric(dim, f"{score:.0f}/1000")
            
            # === SECTION 2: COMPARAISON RÉGIONALE ===
            st.markdown('<div class="section-header">📈 COMPARAISON RÉGIONALE</div>', unsafe_allow_html=True)
            
            comparison_fig = create_comparison_chart(scores["dimensions"], benchmark_scores)
            st.plotly_chart(comparison_fig, use_container_width=True)
            
            # Tableau de comparaison
            comparison_data = []
            for dim in scores["dimensions"].keys():
                diff = scores["dimensions"][dim] - benchmark_scores[dim]
                comparison_data.append({
                    "Dimension": dim,
                    f"{city_name}": f"{scores['dimensions'][dim]:.0f}",
                    "Benchmark régional": f"{benchmark_scores[dim]:.0f}",
                    "Écart": f"{diff:+.0f}",
                    "Performance": "✓ Au-dessus" if diff > 0 else "✗ En-dessous"
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            st.dataframe(df_comparison, use_container_width=True, hide_index=True)
            
            # === SECTION 3: DASHBOARD INFRASTRUCTURES ===
            st.markdown('<div class="section-header">🏗️ DASHBOARD DES INFRASTRUCTURES</div>', unsafe_allow_html=True)
            
            infra_dashboard = create_infrastructure_dashboard(water_access, electricity_access, sanitation_access, internet_access)
            st.plotly_chart(infra_dashboard, use_container_width=True)
            
            # === SECTION 4: ÉVOLUTION DÉMOGRAPHIQUE ===
            st.markdown('<div class="section-header">👥 PROJECTION DÉMOGRAPHIQUE</div>', unsafe_allow_html=True)
            
            demo_fig = create_demographic_evolution_chart(population, growth_rate)
            st.plotly_chart(demo_fig, use_container_width=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                pop_2030 = int(population * ((1 + growth_rate/100) ** 5))
                st.metric("Population 2030", f"{pop_2030:,}".replace(",", " "), f"+{pop_2030-population:,}".replace(",", " "))
            with col2:
                st.metric("Densité actuelle", f"{density:.0f} hab/km²")
            with col3:
                st.metric("Jeunes (0-25 ans)", f"{youth_percentage}%")
            with col4:
                st.metric("Croissance annuelle", f"{growth_rate}%")
            
            # === SECTION 5: SCÉNARIOS WHAT-IF ===
            st.markdown('<div class="section-header">🎯 SCÉNARIOS D\'INTERVENTION (WHAT-IF)</div>', unsafe_allow_html=True)
            
            scenario_tabs = st.tabs(["💧 Eau potable", "⚡ Électricité", "🏠 Logement", "📚 Éducation"])
            
            # Scénario 1: Eau
            with scenario_tabs[0]:
                st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
                st.subheader("Scénario: Amélioration de l'accès à l'eau potable")
                
                col_param, col_result = st.columns(2)
                
                with col_param:
                    st.write("**Paramètres du scénario:**")
                    water_target = st.slider(
                        "Objectif d'accès à l'eau (%)",
                        min_value=water_access,
                        max_value=100,
                        value=min(water_access + 30, 90),
                        key="water_scenario"
                    )
                    
                    costs_water = calculate_scenario_costs("eau", population, water_access, water_target)
                    
                    st.write(f"**Population ciblée:** {costs_water['population_cible']:,} habitants".replace(",", " "))
                    st.write(f"**Coût total:** {costs_water['cout_total_eur']:,.0f} €".replace(",", " "))
                    st.write(f"**Coût par habitant:** {costs_water['cout_par_hab_eur']:.0f} €")
                
                with col_result:
                    st.write("**Impacts estimés:**")
                    
                    # Recalcul des scores
                    new_scores_water = compute_scores(
                        water_target, electricity_access, sanitation_access, internet_access, road_quality,
                        housing_deficit, informal_settlements, housing_cost,
                        unemployment_rate, informal_economy, gdp_per_capita,
                        literacy_rate, infant_mortality, life_expectancy,
                        green_spaces, air_quality, waste_management,
                        public_transport, traffic_congestion,
                        youth_percentage, density, population
                    )
                    
                    delta_global = new_scores_water["score_global"] - scores["score_global"]
                    delta_infra = new_scores_water["dimensions"]["Infrastructures"] - scores["dimensions"]["Infrastructures"]
                    
                    st.metric("Nouveau score global", f"{new_scores_water['score_global']:.0f}/1000", f"{delta_global:+.0f} pts")
                    st.metric("Score Infrastructures", f"{new_scores_water['dimensions']['Infrastructures']:.0f}/1000", f"{delta_infra:+.0f} pts")
                    st.metric("Bénéfices santé", f"{costs_water['benefices_sante']:,} personnes".replace(",", " "))
                    st.metric("Bénéfices économiques/an", f"{costs_water['benefices_economiques_annuels']:,.0f} €".replace(",", " "))
                    st.metric("Retour sur investissement", f"{costs_water['retour_investissement_ans']} ans")
                
                st.markdown("**💡 Analyse:**")
                st.info(f"""
                En portant l'accès à l'eau potable de {water_access}% à {water_target}%, le score global de {city_name} 
                progresserait de {delta_global:+.0f} points. Environ {costs_water['population_cible']:,} habitants 
                bénéficieraient directement de cette amélioration, pour un investissement de {costs_water['cout_total_eur']:,.0f} €. 
                Les bénéfices économiques annuels sont estimés à {costs_water['benefices_economiques_annuels']:,.0f} €, 
                avec un retour sur investissement en {costs_water['retour_investissement_ans']} ans.
                """.replace(",", " "))
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Scénario 2: Électricité
            with scenario_tabs[1]:
                st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
                st.subheader("Scénario: Extension du réseau électrique")
                
                col_param, col_result = st.columns(2)
                
                with col_param:
                    st.write("**Paramètres du scénario:**")
                    elec_target = st.slider(
                        "Objectif d'accès à l'électricité (%)",
                        min_value=electricity_access,
                        max_value=100,
                        value=min(electricity_access + 25, 85),
                        key="elec_scenario"
                    )
                    
                    costs_elec = calculate_scenario_costs("electricite", population, electricity_access, elec_target)
                    
                    st.write(f"**Population ciblée:** {costs_elec['population_cible']:,} habitants".replace(",", " "))
                    st.write(f"**Coût total:** {costs_elec['cout_total_eur']:,.0f} €".replace(",", " "))
                    st.write(f"**Coût par habitant:** {costs_elec['cout_par_hab_eur']:.0f} €")
                
                with col_result:
                    st.write("**Impacts estimés:**")
                    
                    new_scores_elec = compute_scores(
                        water_access, elec_target, sanitation_access, internet_access, road_quality,
                        housing_deficit, informal_settlements, housing_cost,
                        unemployment_rate, informal_economy, gdp_per_capita,
                        literacy_rate, infant_mortality, life_expectancy,
                        green_spaces, air_quality, waste_management,
                        public_transport, traffic_congestion,
                        youth_percentage, density, population
                    )
                    
                    delta_global = new_scores_elec["score_global"] - scores["score_global"]
                    
                    st.metric("Nouveau score global", f"{new_scores_elec['score_global']:.0f}/1000", f"{delta_global:+.0f} pts")
                    st.metric("Emplois créés", f"{costs_elec['creation_emplois']:,}".replace(",", " "))
                    st.metric("Bénéfices économiques/an", f"{costs_elec['benefices_economiques_annuels']:,.0f} €".replace(",", " "))
                    st.metric("Retour sur investissement", f"{costs_elec['retour_investissement_ans']} ans")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Scénario 3: Logement
            with scenario_tabs[2]:
                st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
                st.subheader("Scénario: Programme de construction de logements")
                
                col_param, col_result = st.columns(2)
                
                with col_param:
                    st.write("**Paramètres du scénario:**")
                    housing_reduction = st.slider(
                        "Réduction du déficit en logements",
                        min_value=0,
                        max_value=housing_deficit,
                        value=int(housing_deficit * 0.3),
                        step=1000,
                        key="housing_scenario"
                    )
                    
                    costs_housing = calculate_scenario_costs("logement", population, 0, housing_reduction)
                    
                    st.write(f"**Logements à construire:** {costs_housing['nb_logements']:,}".replace(",", " "))
                    st.write(f"**Coût total:** {costs_housing['cout_total_eur']:,.0f} €".replace(",", " "))
                    st.write(f"**Coût par logement:** {costs_housing['cout_par_logement_eur']:,.0f} €".replace(",", " "))
                
                with col_result:
                    st.write("**Impacts estimés:**")
                    
                    new_housing_deficit = housing_deficit - housing_reduction
                    
                    new_scores_housing = compute_scores(
                        water_access, electricity_access, sanitation_access, internet_access, road_quality,
                        new_housing_deficit, informal_settlements, housing_cost,
                        unemployment_rate, informal_economy, gdp_per_capita,
                        literacy_rate, infant_mortality, life_expectancy,
                        green_spaces, air_quality, waste_management,
                        public_transport, traffic_congestion,
                        youth_percentage, density, population
                    )
                    
                    delta_global = new_scores_housing["score_global"] - scores["score_global"]
                    
                    st.metric("Nouveau score global", f"{new_scores_housing['score_global']:.0f}/1000", f"{delta_global:+.0f} pts")
                    st.metric("Population bénéficiaire", f"{costs_housing['population_beneficiaire']:,}".replace(",", " "))
                    st.metric("Bénéfices sociaux/an", f"{costs_housing['benefices_sociaux_annuels']:,.0f} €".replace(",", " "))
                    st.metric("Retour sur investissement", f"{costs_housing['retour_investissement_ans']} ans")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Scénario 4: Éducation
            with scenario_tabs[3]:
                st.markdown('<div class="scenario-box">', unsafe_allow_html=True)
                st.subheader("Scénario: Programme d'alphabétisation")
                
                col_param, col_result = st.columns(2)
                
                with col_param:
                    st.write("**Paramètres du scénario:**")
                    literacy_target = st.slider(
                        "Objectif taux d'alphabétisation (%)",
                        min_value=literacy_rate,
                        max_value=100,
                        value=min(literacy_rate + 15, 90),
                        key="literacy_scenario"
                    )
                    
                    costs_edu = calculate_scenario_costs("education", population, literacy_rate, literacy_target)
                    
                    st.write(f"**Population ciblée:** {costs_edu['population_cible']:,} personnes".replace(",", " "))
                    st.write(f"**Coût total:** {costs_edu['cout_total_eur']:,.0f} €".replace(",", " "))
                    st.write(f"**Coût par personne:** {costs_edu['cout_par_personne_eur']:.0f} €")
                
                with col_result:
                    st.write("**Impacts estimés:**")
                    
                    new_scores_edu = compute_scores(
                        water_access, electricity_access, sanitation_access, internet_access, road_quality,
                        housing_deficit, informal_settlements, housing_cost,
                        unemployment_rate, informal_economy, gdp_per_capita,
                        literacy_target, infant_mortality, life_expectancy,
                        green_spaces, air_quality, waste_management,
                        public_transport, traffic_congestion,
                        youth_percentage, density, population
                    )
                    
                    delta_global = new_scores_edu["score_global"] - scores["score_global"]
                    
                    st.metric("Nouveau score global", f"{new_scores_edu['score_global']:.0f}/1000", f"{delta_global:+.0f} pts")
                    st.metric("Bénéfices économiques/an", f"{costs_edu['benefices_economiques_annuels']:,.0f} €".replace(",", " "))
                    st.metric("Retour sur investissement", f"{costs_edu['retour_investissement_ans']} ans")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # === SECTION 6: RAPPORT PDF ===
            st.markdown('<div class="section-header">📥 TÉLÉCHARGER LE RAPPORT</div>', unsafe_allow_html=True)
            
            executive_prompt = f"""
            Rédigez un résumé exécutif professionnel de 300 mots pour le diagnostic urbain de {city_name}, {country}.
            Population: {population:,} habitants, croissance: {growth_rate}%.
            Score global: {scores['score_global']:.0f}/1000.
            Principaux défis: accès eau {water_access}%, électricité {electricity_access}%, habitat informel {informal_settlements}%.
            Style: professionnel, sans emojis, paragraphes structurés.
            """
            
            executive_summary = generate_enhanced_content(executive_prompt, clients, 500)
            
            report_data = {
                "executive_summary": executive_summary,
                "score_global": scores["score_global"]
            }
            
            pdf_buffer = generate_professional_pdf_report(city_name, country, report_data)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📄 Télécharger le rapport PDF complet",
                    data=pdf_buffer,
                    file_name=f"Diagnostic_{city_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        st.success("✅ Diagnostic généré avec succès !")
    
    else:
        st.info("👈 Remplissez le formulaire à gauche puis cliquez sur 'Générer le rapport complet' pour lancer le diagnostic urbain.")

def main():
    create_header()
    tabs = st.tabs(["🏙️ Diagnostic", "🎓 Coach Urbain"])
    with tabs[0]:
        diagnostic_tab()
    with tabs[1]:
        coach_urbain_tab()

if __name__ == "__main__":
    main()
