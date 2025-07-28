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

# Configuration de la page
st.set_page_config(
    page_title="AfricanCities IA Services",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS pour améliorer l'apparence
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
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .toc-item {
        padding: 0.3rem 0;
        border-bottom: 1px dotted #ccc;
        display: flex;
        justify-content: space-between;
    }
    .professional-text {
        text-align: justify;
        line-height: 1.6;
        color: #2c3e50;
        font-size: 1rem;
    }
    .form-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

def create_header():
    """Crée le header avec logo et titres"""
    st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            🏙️
        </div>
        <div class="main-title">AfricanCities IA Services</div>
        <div class="subtitle">Diagnostiquer, comprendre, transformer votre ville</div>
        <div class="institution">Centre of Urban Systems - UM6P</div>
    </div>
    """, unsafe_allow_html=True)

def initialize_ai_clients():
    """Initialise les clients IA"""
    clients = {}
    if st.secrets.get("OPENAI_API_KEY"):
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        clients['openai'] = True
    if st.secrets.get("GROQ_API_KEY"):
        clients['groq'] = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return clients

def extract_text_from_pdf(pdf_file):
    """Extrait le texte d'un fichier PDF avec OCR si nécessaire"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if len(text.strip()) < 100:
            st.warning("Peu de texte détecté dans ce PDF. Le document pourrait être scanné ou contenir principalement des images.")
        return text.strip()
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte: {str(e)}")
        return ""

def process_uploaded_documents(uploaded_files):
    """Traite tous les documents uploadés et extrait leur contenu"""
    documents_content = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.info(f"Traitement du document: {uploaded_file.name}")
            if uploaded_file.type == "application/pdf":
                uploaded_file.seek(0)
                text_content = extract_text_from_pdf(uploaded_file)
                if text_content:
                    documents_content.append({
                        'filename': uploaded_file.name,
                        'content': text_content[:5000]  # Limiter à 5000 caractères par document
                    })
                    st.success(f"✅ Document {uploaded_file.name} traité avec succès")
                else:
                    st.warning(f"⚠️ Aucun texte extrait de {uploaded_file.name}")
    return documents_content

def generate_enhanced_content_with_docs(prompt, clients, documents_content=None, max_tokens=800):
    """Génère du contenu enrichi en incluant les documents uploadés"""
    try:
        enhanced_prompt = prompt
        if documents_content and len(documents_content) > 0:
            docs_text = "\n\nDOCUMENTS TECHNIQUES FOURNIS :\n"
            for i, doc in enumerate(documents_content, 1):
                docs_text += f"\n--- Document {i}: {doc['filename']} ---\n"
                docs_text += doc['content'][:2000]
                docs_text += "\n"
            enhanced_prompt = prompt + docs_text + "\n\nVeuillez intégrer les informations de ces documents techniques dans votre analyse."
        if 'groq' in clients:
            response = clients['groq'].chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Analysez les documents fournis et intégrez leurs informations dans vos réponses. Rédigez du contenu professionnel, détaillé et précis sans emojis."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
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
                    {"role": "system", "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Analysez les documents fournis et intégrez leurs informations dans vos réponses. Rédigez du contenu professionnel, détaillé et précis sans emojis."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            return "Contenu générique - Aucun client IA disponible"
    except Exception as e:
        st.error(f"Erreur lors de la génération de contenu: {str(e)}")
        return f"Erreur de génération pour: {prompt[:50]}..."

# (Les fonctions create_demographic_chart, create_infrastructure_chart, create_housing_analysis_chart, generate_professional_pdf_report, dashboard_tab, chatbot_tab restent inchangées, tu peux les garder telles quelles dans ton code d'origine.)

# Seule la fonction diagnostic_tab est modifiée pour intégrer les documents dans les prompts :

def diagnostic_tab():
    """Onglet Diagnostic avec formulaire détaillé"""
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
        with st.spinner("Génération du rapport en cours..."):
            documents_content = process_uploaded_documents(uploaded_files)
            if documents_content:
                st.success(f"📄 {len(documents_content)} document(s) analysé(s) et intégré(s) dans le rapport")
                with st.expander("📋 Aperçu des documents traités"):
                    for doc in documents_content:
                        st.write(f"**{doc['filename']}**")
                        st.write(f"Extrait: {doc['content'][:200]}...")
                        st.write("---")
            st.info(f"""
            **Diagnostic configuré pour:** {city_name}, {country}  
            **Type:** {diagnostic_type}  
            **Population:** {population:,} habitants  
            **Date:** {diagnostic_date.strftime('%d/%m/%Y')}
            **Documents analysés:** {len(documents_content) if documents_content else 0}
            """)
            # Table des matières dynamique, etc. (inchangé)
            # Pour chaque section, utiliser generate_enhanced_content_with_docs au lieu de generate_enhanced_content
            executive_prompt = f"""
            Rédigez un résumé exécutif professionnel de 400 mots pour le diagnostic urbain de {city_name}, {country}.
            Type de diagnostic: {diagnostic_type}
            Objectif: {diagnostic_objective}
            Population: {population:,} habitants, croissance: {growth_rate}%.
            Accès eau: {water_access}%, électricité: {electricity_access}%, assainissement: {sanitation_access}%.
            Chômage: {unemployment_rate}%, habitat informel: {informal_settlements}%.
            Risques climatiques: {', '.join(climate_risks) if climate_risks else 'Non spécifiés'}.
            Contexte particulier: {additional_comments if additional_comments else 'Aucun commentaire spécifique'}.
            Incluez: situation actuelle, défis principaux, opportunités, recommandations clés.
            Style: professionnel, sans emojis, paragraphes structurés.
            """
            executive_summary = generate_enhanced_content_with_docs(executive_prompt, clients, documents_content, 600)
            st.markdown(f'<div class="professional-text">{executive_summary}</div>', unsafe_allow_html=True)
            # ... (idem pour les autres sections du rapport, toujours en passant documents_content)
            # Le reste du code de diagnostic_tab reste inchangé, sauf que tu utilises toujours generate_enhanced_content_with_docs pour chaque section.

def main():
    create_header()
    tab1, tab2, tab3 = st.tabs(["🏙️ Diagnostic", "📊 Dashboard", "🤖 Chatbot"])
    with tab1:
        diagnostic_tab()
    with tab2:
        dashboard_tab()
    with tab3:
        chatbot_tab()

if __name__ == "__main__":
    main()
