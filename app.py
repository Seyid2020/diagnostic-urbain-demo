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
    
    # OpenAI
    if st.secrets.get("OPENAI_API_KEY"):
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        clients['openai'] = True
    
    # Groq
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
                # Réinitialiser le pointeur du fichier
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
        # Construire le prompt avec les documents si disponibles
        enhanced_prompt = prompt
        
        if documents_content and len(documents_content) > 0:
            docs_text = "\n\nDOCUMENTS TECHNIQUES FOURNIS :\n"
            for i, doc in enumerate(documents_content, 1):
                docs_text += f"\n--- Document {i}: {doc['filename']} ---\n"
                docs_text += doc['content'][:2000]  # Limiter chaque document à 2000 caractères
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

def generate_enhanced_content(prompt, clients, max_tokens=800):
    """Génère du contenu enrichi avec gestion des limites (fonction de compatibilité)"""
    return generate_enhanced_content_with_docs(prompt, clients, None, max_tokens)

def create_demographic_chart(city_data):
    """Crée un graphique démographique"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Répartition par âge', 'Croissance démographique', 
                       'Densité urbaine', 'Migration urbaine'),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    # Graphique en secteurs pour les groupes d'âge
    age_groups = ['0-14 ans', '15-64 ans', '65+ ans']
    age_values = [42.5, 54.3, 3.2]
    
    fig.add_trace(
        go.Pie(labels=age_groups, values=age_values, name="Âge"),
        row=1, col=1
    )
    
    # Graphique de croissance
    years = ['2018', '2019', '2020', '2021', '2022']
    population = [1050000, 1087500, 1126250, 1165656, 1206428]
    
    fig.add_trace(
        go.Bar(x=years, y=population, name="Population"),
        row=1, col=2
    )
    
    # Densité urbaine
    districts = ['Centre', 'Nord', 'Sud', 'Est', 'Ouest']
    density = [8500, 6200, 4800, 5500, 7200]
    
    fig.add_trace(
        go.Scatter(x=districts, y=density, mode='markers+lines', name="Densité"),
        row=2, col=1
    )
    
    # Migration
    migration_data = ['Arrivées', 'Départs', 'Solde migratoire']
    migration_values = [45000, 28000, 17000]
    
    fig.add_trace(
        go.Bar(x=migration_data, y=migration_values, name="Migration"),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="Analyse Démographique Complète")
    return fig

def create_infrastructure_chart():
    """Crée un graphique d'infrastructure"""
    categories = ['Eau potable', 'Électricité', 'Assainissement', 'Routes', 'Télécommunications']
    current_access = [45, 42, 25, 60, 78]
    target_access = [80, 75, 60, 85, 90]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Accès actuel (%)',
        x=categories,
        y=current_access,
        marker_color='lightcoral'
    ))
    
    fig.add_trace(go.Bar(
        name='Objectif 2030 (%)',
        x=categories,
        y=target_access,
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title='État des Infrastructures de Base',
        xaxis_title='Services',
        yaxis_title='Taux d\'accès (%)',
        barmode='group',
        height=400
    )
    
    return fig

def create_housing_analysis_chart():
    """Crée un graphique d'analyse du logement"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Types de logement', 'Qualité du logement'),
        specs=[[{"type": "pie"}, {"type": "bar"}]]
    )
    
    # Types de logement
    housing_types = ['Béton/Dur', 'Semi-dur', 'Traditionnel', 'Précaire']
    housing_values = [35, 25, 25, 15]
    
    fig.add_trace(
        go.Pie(labels=housing_types, values=housing_values, name="Types"),
        row=1, col=1
    )
    
    # Qualité du logement
    quality_aspects = ['Eau courante', 'Électricité', 'Toilettes', 'Cuisine équipée']
    quality_percentages = [45, 42, 12, 28]
    
    fig.add_trace(
        go.Bar(x=quality_aspects, y=quality_percentages, name="Qualité"),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False)
    return fig

def generate_professional_pdf_report(city_name, report_data, charts_data):
    """Génère un rapport PDF professionnel"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Styles
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
    story.append(Paragraph(f"Ville de {city_name}", title_style))
    story.append(Spacer(1, 50))
    story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", body_style))
    story.append(Paragraph("UrbanAI Diagnostic Platform", body_style))
    story.append(PageBreak())
    
    # Table des matières
    story.append(Paragraph("TABLE DES MATIÈRES", section_style))
    toc_data = [
        ["Section", "Page"],
        ["1. Résumé exécutif", "3"],
        ["2. Contexte démographique et social", "5"],
        ["3. Analyse de l'habitat et des infrastructures", "8"],
        ["4. Défis et opportunités identifiés", "11"],
        ["5. Recommandations stratégiques", "14"],
        ["6. Graphiques et visualisations", "17"],
        ["7. Conclusion prospective", "19"],
        ["Annexes et références", "21"]
    ]
    
    toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(toc_table)
    story.append(PageBreak())
    
    # Contenu des sections
    sections = [
        ("1. RÉSUMÉ EXÉCUTIF", report_data.get('executive_summary', '')),
        ("2. CONTEXTE DÉMOGRAPHIQUE ET SOCIAL", report_data.get('demographic_context', '')),
        ("3. ANALYSE DE L'HABITAT ET DES INFRASTRUCTURES", report_data.get('housing_analysis', '')),
        ("4. DÉFIS ET OPPORTUNITÉS IDENTIFIÉS", report_data.get('challenges', '')),
        ("5. RECOMMANDATIONS STRATÉGIQUES", report_data.get('recommendations', '')),
        ("6. GRAPHIQUES ET VISUALISATIONS", "Les graphiques détaillés sont présentés dans l'interface web interactive."),
        ("7. CONCLUSION PROSPECTIVE", report_data.get('conclusion', ''))
    ]
    
    for section_title, content in sections:
        story.append(Paragraph(section_title, section_style))
        story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 20))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def diagnostic_tab():
    """Onglet Diagnostic avec formulaire détaillé"""
    st.markdown('<div class="main-header">🏙️ DIAGNOSTIC URBAIN INTELLIGENT</div>', unsafe_allow_html=True)
    
    # Initialisation des clients IA
    clients = initialize_ai_clients()
    
    # Formulaire détaillé dans la sidebar
    with st.sidebar:
        st.header("⚙️ Configuration du Diagnostic")
        
        # Informations générales
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🌍 Informations Générales")
        city_name = st.text_input("Nom de la ville", value="Nouakchott")
        country = st.text_input("Pays", value="Mauritanie")
        region = st.text_input("Région/Province", value="Nouakchott")
        diagnostic_date = st.date_input("Date du diagnostic", value=datetime.now())
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Données démographiques
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("👥 Données Démographiques")
        population = st.number_input("Population totale (habitants)", value=1200000, step=10000)
        growth_rate = st.number_input("Taux de croissance annuel (%)", value=3.5, step=0.1)
        urban_area = st.number_input("Superficie urbaine (km²)", value=1000, step=10)
        density = st.number_input("Densité urbaine (hab/km²)", value=int(population/urban_area), step=100)
        youth_percentage = st.slider("Pourcentage de jeunes (0-25 ans) (%)", 0, 100, 60)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Infrastructures de base
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🏗️ Infrastructures de Base")
        water_access = st.slider("Accès à l'eau potable (%)", 0, 100, 45)
        electricity_access = st.slider("Accès à l'électricité (%)", 0, 100, 42)
        sanitation_access = st.slider("Accès à l'assainissement (%)", 0, 100, 25)
        road_quality = st.selectbox("Qualité du réseau routier", ["Très mauvaise", "Mauvaise", "Moyenne", "Bonne", "Très bonne"])
        internet_access = st.slider("Accès à Internet (%)", 0, 100, 35)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Logement et habitat
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
        
        # Économie et emploi
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
        
        # Services sociaux
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🏥 Services Sociaux")
        health_facilities = st.number_input("Nombre d'établissements de santé", value=15, step=1)
        schools = st.number_input("Nombre d'écoles", value=120, step=5)
        literacy_rate = st.slider("Taux d'alphabétisation (%)", 0, 100, 65)
        infant_mortality = st.number_input("Mortalité infantile (pour 1000)", value=45, step=1)
        life_expectancy = st.number_input("Espérance de vie (années)", value=65, step=1)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Environnement et climat
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
        
        # Transport et mobilité
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🚌 Transport et Mobilité")
        public_transport = st.selectbox("Transport public", ["Inexistant", "Très limité", "Limité", "Développé", "Très développé"])
        vehicle_ownership = st.slider("Taux de motorisation (véhicules/1000 hab)", 0, 500, 80)
        traffic_congestion = st.selectbox("Congestion routière", ["Très faible", "Faible", "Modérée", "Forte", "Très forte"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Documents techniques
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("📄 Documents Techniques")
        uploaded_files = st.file_uploader(
            "Télécharger des documents (PDF)",
            type=['pdf'],
            accept_multiple_files=True,
            help="Plans d'urbanisme, études, rapports, etc."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Type et objectif du diagnostic
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
        
        # Commentaires libres
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("💭 Commentaires et Observations")
        additional_comments = st.text_area(
            "Commentaires libres, contexte particulier, défis spécifiques...",
            height=120,
            placeholder="Décrivez ici tout élément de contexte important, défis particuliers, projets en cours, etc."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        generate_report = st.button("🚀 Générer le rapport complet", type="primary", use_container_width=True)
    
    # Interface principale pour le rapport
    if generate_report:
        with st.spinner("Génération du rapport en cours..."):
            
            # Traitement des documents uploadés
            documents_content = process_uploaded_documents(uploaded_files)
            
            if documents_content:
                st.success(f"📄 {len(documents_content)} document(s) analysé(s) et intégré(s) dans le rapport")
                
                # Afficher un aperçu des documents traités
                with st.expander("📋 Aperçu des documents traités"):
                    for doc in documents_content:
                        st.write(f"**{doc['filename']}**")
                        st.write(f"Extrait: {doc['content'][:200]}...")
                        st.write("---")
            
            # Affichage des informations de configuration
            st.info(f"""
            **Diagnostic configuré pour:** {city_name}, {country}  
            **Type:** {diagnostic_type}  
            **Population:** {population:,} habitants  
            **Date:** {diagnostic_date.strftime('%d/%m/%Y')}
            **Documents analysés:** {len(documents_content) if documents_content else 0}
            """)
            
            # Table des matières dynamique
            st.markdown('<div class="section-header">📋 TABLE DES MATIÈRES</div>', unsafe_allow_html=True)
            
            toc_items = [
                ("1. Résumé exécutif", "3"),
                ("2. Contexte démographique et social", "5"),
                ("3. Analyse de l'habitat et des infrastructures", "8"),
                ("4. Défis et opportunités identifiés", "11"),
                ("5. Recommandations stratégiques", "14"),
                ("6. Graphiques et visualisations", "17"),
                ("7. Conclusion prospective", "19")
            ]
            
            for item, page in toc_items:
                st.markdown(f'<div class="toc-item"><span>{item}</span><span>Page {page}</span></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 1. RÉSUMÉ EXÉCUTIF
            st.markdown('<div class="section-header">1. RÉSUMÉ EXÉCUTIF</div>', unsafe_allow_html=True)
            
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
            
            # 2. CONTEXTE DÉMOGRAPHIQUE ET SOCIAL
            st.markdown('<div class="section-header">2. CONTEXTE DÉMOGRAPHIQUE ET SOCIAL</div>', unsafe_allow_html=True)
            
            # 2.1 Profil démographique
            st.markdown('<div class="subsection-header">2.1 Profil démographique</div>', unsafe_allow_html=True)
            
            demo_prompt = f"""
            Analysez le profil démographique de {city_name} avec {population:,} habitants et {growth_rate}% de croissance.
            Densité: {density} hab/km², jeunes (0-25 ans): {youth_percentage}%.
            Détaillez: structure par âge, migration, densité urbaine, projections 2030.
            Comparaisons régionales avec autres capitales sahéliennes.
            300 mots, style analytique professionnel.
            """
            
            demographic_analysis = generate_enhanced_content_with_docs(demo_prompt, clients, documents_content, 500)
            st.markdown(f'<div class="professional-text">{demographic_analysis}</div>', unsafe_allow_html=True)
            
            # Graphique démographique
            demo_chart = create_demographic_chart({"population": population, "growth": growth_rate})
            st.plotly_chart(demo_chart, use_container_width=True)
            
            # 2.2 Contexte socio-économique
            st.markdown('<div class="subsection-header">2.2 Contexte socio-économique</div>', unsafe_allow_html=True)
            
            socio_prompt = f"""
            Analysez le contexte socio-économique de {city_name}:
            - Secteurs économiques dominants: {', '.join(main_sectors) if main_sectors else 'Non spécifiés'}
            - Chômage: {unemployment_rate}%, économie informelle: {informal_economy}%
            - PIB par habitant: {gdp_per_capita} USD
            - Taux d'alphabétisation: {literacy_rate}%
            - Mortalité infantile: {infant_mortality}‰, espérance de vie: {life_expectancy} ans
            - Établissements de santé: {health_facilities}, écoles: {schools}
            350 mots, données chiffrées, analyse approfondie.
            """
            
            socio_analysis = generate_enhanced_content_with_docs(socio_prompt, clients, documents_content, 600)
            st.markdown(f'<div class="professional-text">{socio_analysis}</div>', unsafe_allow_html=True)
            
            # Métriques socio-économiques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Taux de chômage", f"{unemployment_rate}%", "-2.1%")
            with col2:
                st.metric("PIB par habitant", f"{gdp_per_capita} USD", "+4.2%")
            with col3:
                st.metric("Taux d'alphabétisation", f"{literacy_rate}%", "+3.5%")
            with col4:
                st.metric("Économie informelle", f"{informal_economy}%", "-1.8%")
            
            # 3. ANALYSE DE L'HABITAT ET DES INFRASTRUCTURES
            st.markdown('<div class="section-header">3. ANALYSE DE L\'HABITAT ET DES INFRASTRUCTURES</div>', unsafe_allow_html=True)
            
            # 3.1 État du parc de logements
            st.markdown('<div class="subsection-header">3.1 État du parc de logements</div>', unsafe_allow_html=True)
            
            housing_prompt = f"""
            Analysez l'état du parc de logements à {city_name}:
            - Déficit en logements: {housing_deficit:,} unités
            - Population en habitat informel: {informal_settlements}%
            - Coût du logement: {housing_cost} USD/m²
            - Matériaux dominants: {', '.join(construction_materials) if construction_materials else 'Non spécifiés'}
            - Accès eau: {water_access}%, électricité: {electricity_access}%
            Détaillez: types de logements, qualité du bâti, surpeuplement, marché immobilier, quartiers informels.
            400 mots, analyse technique détaillée.
            """
            
            housing_analysis = generate_enhanced_content_with_docs(housing_prompt, clients, documents_content, 700)
            st.markdown(f'<div class="professional-text">{housing_analysis}</div>', unsafe_allow_html=True)
            
            # Graphique logement
            housing_chart = create_housing_analysis_chart()
            st.plotly_chart(housing_chart, use_container_width=True)
            
            # 3.2 Infrastructures de base
            st.markdown('<div class="subsection-header">3.2 Infrastructures de base</div>', unsafe_allow_html=True)
            
            infra_prompt = f"""
            Évaluez les infrastructures de base de {city_name}:
            - Eau potable: {water_access}% de couverture
            - Électricité: {electricity_access}% de couverture
            - Assainissement: {sanitation_access}% de couverture
            - Qualité des routes: {road_quality}
            - Accès Internet: {internet_access}%
            - Gestion des déchets: {waste_management}
            - Transport public: {public_transport}
            450 mots, évaluation technique approfondie.
            """
            
            infrastructure_analysis = generate_enhanced_content_with_docs(infra_prompt, clients, documents_content, 700)
            st.markdown(f'<div class="professional-text">{infrastructure_analysis}</div>', unsafe_allow_html=True)
            
            # Graphique infrastructures
            infra_chart = create_infrastructure_chart()
            st.plotly_chart(infra_chart, use_container_width=True)
            
            # 4. DÉFIS ET OPPORTUNITÉS IDENTIFIÉS
            st.markdown('<div class="section-header">4. DÉFIS ET OPPORTUNITÉS IDENTIFIÉS</div>', unsafe_allow_html=True)
            
            # 4.1 Défis majeurs
            st.markdown('<div class="subsection-header">4.1 Défis majeurs</div>', unsafe_allow_html=True)
            
            challenges_prompt = f"""
            Identifiez et analysez les défis majeurs de {city_name}:
            - Croissance démographique rapide ({growth_rate}%) et planification urbaine
            - Déficit en logements ({housing_deficit:,} unités) et habitat informel ({informal_settlements}%)
            - Insuffisance des services de base (eau: {water_access}%, électricité: {electricity_access}%)
            - Chômage élevé ({unemployment_rate}%) et économie informelle ({informal_economy}%)
            - Risques climatiques: {', '.join(climate_risks) if climate_risks else 'Non spécifiés'}
            - Qualité de l'air: {air_quality}, gestion des déchets: {waste_management}
            400 mots, analyse critique et factuelle.
            """
            
            challenges_analysis = generate_enhanced_content_with_docs(challenges_prompt, clients, documents_content, 700)
            st.markdown(f'<div class="professional-text">{challenges_analysis}</div>', unsafe_allow_html=True)
            
            # 4.2 Opportunités de développement
            st.markdown('<div class="subsection-header">4.2 Opportunités de développement</div>', unsafe_allow_html=True)
            
            opportunities_prompt = f"""
            Analysez les opportunités de développement pour {city_name}:
            - Secteurs économiques porteurs: {', '.join(main_sectors) if main_sectors else 'À identifier'}
            - Population jeune ({youth_percentage}% de moins de 25 ans)
            - Potentiel de développement urbain sur {urban_area} km²
            - Coopération internationale et financement
            - Innovation technologique et villes intelligentes
            - Partenariats public-privé
            350 mots, vision prospective et réaliste.
            """
            
            opportunities_analysis = generate_enhanced_content_with_docs(opportunities_prompt, clients, documents_content, 600)
            st.markdown(f'<div class="professional-text">{opportunities_analysis}</div>', unsafe_allow_html=True)
            
            # 5. RECOMMANDATIONS STRATÉGIQUES
            st.markdown('<div class="section-header">5. RECOMMANDATIONS STRATÉGIQUES</div>', unsafe_allow_html=True)
            
            # 5.1 Priorités à court terme (1-3 ans)
            st.markdown('<div class="subsection-header">5.1 Priorités à court terme (1-3 ans)</div>', unsafe_allow_html=True)
            
            short_term_prompt = f"""
            Formulez des recommandations prioritaires à court terme pour {city_name}:
            - Amélioration urgente de l'accès à l'eau potable (actuellement {water_access}%)
            - Extension du réseau électrique (actuellement {electricity_access}%)
            - Programmes d'urgence pour l'habitat précaire ({informal_settlements}% de la population)
            - Création d'emplois face au chômage de {unemployment_rate}%
            - Renforcement des capacités institutionnelles
            - Gestion des risques climatiques: {', '.join(climate_risks) if climate_risks else 'À définir'}
            300 mots, recommandations concrètes et réalisables.
            """
            
            short_term_reco = generate_enhanced_content_with_docs(short_term_prompt, clients, documents_content, 500)
            st.markdown(f'<div class="professional-text">{short_term_reco}</div>', unsafe_allow_html=True)
            
            # 5.2 Stratégies à moyen terme (3-7 ans)
            st.markdown('<div class="subsection-header">5.2 Stratégies à moyen terme (3-7 ans)</div>', unsafe_allow_html=True)
            
            medium_term_prompt = f"""
            Développez des stratégies à moyen terme pour {city_name}:
            - Planification urbaine intégrée pour gérer la croissance de {growth_rate}%
            - Développement de nouveaux quartiers planifiés
            - Modernisation des infrastructures existantes
            - Diversification économique (secteurs actuels: {', '.join(main_sectors) if main_sectors else 'À développer'})
            - Renforcement de la résilience climatique
            - Amélioration du transport public (actuellement: {public_transport})
            350 mots, approche stratégique et intégrée.
            """
            
            medium_term_reco = generate_enhanced_content_with_docs(medium_term_prompt, clients, documents_content, 600)
            st.markdown(f'<div class="professional-text">{medium_term_reco}</div>', unsafe_allow_html=True)
            
            # 5.3 Vision à long terme (7-15 ans)
            st.markdown('<div class="subsection-header">5.3 Vision à long terme (7-15 ans)</div>', unsafe_allow_html=True)
            
            long_term_prompt = f"""
            Esquissez une vision à long terme pour {city_name}:
            - Transformation en ville intelligente et durable
            - Hub économique régional basé sur {', '.join(main_sectors) if main_sectors else 'les secteurs porteurs'}
            - Modèle de développement urbain africain
            - Objectifs de développement durable (ODD 11)
            - Innovation et technologies urbaines
            - Résilience face aux défis climatiques
            300 mots, vision ambitieuse mais réaliste.
            """
            
            long_term_reco = generate_enhanced_content_with_docs(long_term_prompt, clients, documents_content, 500)
            st.markdown(f'<div class="professional-text">{long_term_reco}</div>', unsafe_allow_html=True)
            
            # 6. GRAPHIQUES ET VISUALISATIONS
            st.markdown('<div class="section-header">6. GRAPHIQUES ET VISUALISATIONS</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="subsection-header">6.1 Tableau de bord des indicateurs clés</div>', unsafe_allow_html=True)
            
            # Indicateurs synthétiques
            indicators_data = {
                'Indicateur': ['Accès eau potable', 'Accès électricité', 'Assainissement', 'Logement décent', 'Transport public'],
                'Valeur actuelle': [water_access, electricity_access, sanitation_access, 100-informal_settlements, 30 if public_transport in ["Développé", "Très développé"] else 15],
                'Objectif 2030': [80, 75, 60, 70, 60],
                'Écart': [80-water_access, 75-electricity_access, 60-sanitation_access, 70-(100-informal_settlements), 45]
            }
            
            df_indicators = pd.DataFrame(indicators_data)
            st.dataframe(df_indicators, use_container_width=True)
            
            # Graphique radar des performances
            categories = ['Eau', 'Électricité', 'Assainissement', 'Logement', 'Transport', 'Santé', 'Éducation']
            current_values = [water_access, electricity_access, sanitation_access, 100-informal_settlements, 
                            30 if public_transport in ["Développé", "Très développé"] else 15, 
                            max(0, 100-infant_mortality), literacy_rate]
            target_values = [80, 75, 60, 70, 60, 70, 85]
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=current_values,
                theta=categories,
                fill='toself',
                name='Situation actuelle',
                line_color='red'
            ))
            
            fig_radar.add_trace(go.Scatterpolar(
                r=target_values,
                theta=categories,
                fill='toself',
                name='Objectifs 2030',
                line_color='blue'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Radar des Performances Urbaines"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # 7. CONCLUSION PROSPECTIVE
            st.markdown('<div class="section-header">7. CONCLUSION PROSPECTIVE</div>', unsafe_allow_html=True)
            
            conclusion_prompt = f"""
            Rédigez une conclusion prospective pour le diagnostic de {city_name}:
            - Synthèse des enjeux majeurs identifiés
            - Potentiel de transformation urbaine
            - Conditions de succès des recommandations
            - Rôle dans le développement régional
            - Appel à l'action pour les parties prenantes: {', '.join(target_audience) if target_audience else 'toutes les parties prenantes'}
            Contexte spécifique: {additional_comments if additional_comments else 'Aucun élément particulier'}
            400 mots, ton prospectif et mobilisateur.
            """
            
            conclusion = generate_enhanced_content_with_docs(conclusion_prompt, clients, documents_content, 700)
            st.markdown(f'<div class="professional-text">{conclusion}</div>', unsafe_allow_html=True)
            
            # Génération du PDF
            st.markdown("---")
            st.subheader("📄 Téléchargement du rapport")
            
            report_data = {
                'executive_summary': executive_summary,
                'demographic_context': demographic_analysis + " " + socio_analysis,
                'housing_analysis': housing_analysis + " " + infrastructure_analysis,
                'challenges': challenges_analysis + " " + opportunities_analysis,
                'recommendations': short_term_reco + " " + medium_term_reco + " " + long_term_reco,
                'conclusion': conclusion
            }
            
            pdf_buffer = generate_professional_pdf_report(city_name, report_data, {})
            
            st.download_button(
                label="📥 Télécharger le rapport PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"Diagnostic_Urbain_{city_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ Rapport généré avec succès!")
            
            # Métadonnées du rapport
            st.markdown("---")
            st.markdown("### 📋 Métadonnées du rapport")
            st.info(f"""
            **Ville analysée:** {city_name}, {country}  
            **Type de diagnostic:** {diagnostic_type}  
            **Date de génération:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}  
            **Population:** {population:,} habitants  
            **Taux de croissance:** {growth_rate}%  
            **Public cible:** {', '.join(target_audience) if target_audience else 'Non spécifié'}  
            **Documents analysés:** {len(documents_content) if documents_content else 0}  
            **Plateforme:** UrbanAI Diagnostic Platform v2.0
            """)

def dashboard_tab():
    """Onglet Dashboard avec visualisations interactives"""
    st.markdown('<div class="main-header">📊 TABLEAU DE BORD URBAIN</div>', unsafe_allow_html=True)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Population urbaine",
            value="1.2M",
            delta="3.5%",
            help="Croissance annuelle de la population"
        )
    
    with col2:
        st.metric(
            label="Accès à l'eau",
            value="45%",
            delta="-5%",
            delta_color="inverse",
            help="Pourcentage de la population avec accès à l'eau potable"
        )
    
    with col3:
        st.metric(
            label="Taux de chômage",
            value="23.4%",
            delta="-2.1%",
            delta_color="inverse",
            help="Évolution du taux de chômage"
        )
    
    with col4:
        st.metric(
            label="PIB par habitant",
            value="1,850 USD",
            delta="4.2%",
            help="Croissance du PIB par habitant"
        )
    
    st.markdown("---")
    
    # Graphiques interactifs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏠 Accès aux Services de Base")
        
        # Graphique en barres pour les services
        services_data = {
            'Service': ['Eau potable', 'Électricité', 'Assainissement', 'Internet', 'Transport public'],
            'Accès (%)': [45, 42, 25, 35, 20],
            'Objectif 2030 (%)': [80, 75, 60, 70, 50]
        }
        
        df_services = pd.DataFrame(services_data)
        
        fig_services = px.bar(
            df_services, 
            x='Service', 
            y=['Accès (%)', 'Objectif 2030 (%)'],
            title="Accès aux Services vs Objectifs 2030",
            barmode='group',
            color_discrete_map={'Accès (%)': '#ff7f7f', 'Objectif 2030 (%)': '#7fbfff'}
        )
        
        st.plotly_chart(fig_services, use_container_width=True)
    
    with col2:
        st.subheader("👥 Structure Démographique")
        
        # Graphique en secteurs pour les groupes d'âge
        age_data = {
            'Groupe d\'âge': ['0-14 ans', '15-64 ans', '65+ ans'],
            'Population (%)': [42.5, 54.3, 3.2]
        }
        
        fig_age = px.pie(
            values=age_data['Population (%)'],
            names=age_data['Groupe d\'âge'],
            title="Répartition par Groupe d'Âge"
        )
        
        st.plotly_chart(fig_age, use_container_width=True)
    
    # Graphique de tendance
    st.subheader("📈 Évolution de la Population")
    
    years = list(range(2015, 2026))
    population_data = [950000, 985000, 1020000, 1055000, 1090000, 1125000, 1160000, 1195000, 1230000, 1265000, 1300000]
    
    fig_trend = px.line(
        x=years,
        y=population_data,
        title="Croissance Démographique 2015-2025",
        labels={'x': 'Année', 'y': 'Population'}
    )
    
    fig_trend.add_scatter(
        x=[2022], 
        y=[1200000], 
        mode='markers', 
        marker=dict(size=10, color='red'),
        name='Situation actuelle'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Carte de chaleur des indicateurs
    st.subheader("🗺️ Carte de Performance par Secteur")
    
    sectors = ['Centre', 'Nord', 'Sud', 'Est', 'Ouest']
    indicators = ['Eau', 'Électricité', 'Assainissement', 'Routes', 'Santé', 'Éducation']
    
    # Données simulées pour la carte de chaleur
    np.random.seed(42)
    heatmap_data = np.random.randint(20, 80, size=(len(sectors), len(indicators)))
    
    fig_heatmap = px.imshow(
        heatmap_data,
        x=indicators,
        y=sectors,
        title="Performance par Secteur Géographique (%)",
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Indicateurs de performance
    st.subheader("🎯 Indicateurs de Performance Clés")
    
    kpi_data = {
        'Indicateur': [
            'Densité urbaine (hab/km²)',
            'Espaces verts (m²/hab)',
            'Déchets collectés (%)',
            'Mortalité infantile (‰)',
            'Taux d\'alphabétisation (%)',
            'Accès aux soins (min)'
        ],
        'Valeur actuelle': [1200, 5, 60, 45, 65, 25],
        'Objectif': [1000, 15, 90, 25, 85, 15],
        'Statut': ['🔴', '🔴', '🟡', '🔴', '🟡', '🔴']
    }
    
    df_kpi = pd.DataFrame(kpi_data)
    st.dataframe(df_kpi, use_container_width=True)
    
    # Analyse comparative
    st.subheader("🌍 Comparaison Régionale")
    
    cities_comparison = {
        'Ville': ['Nouakchott', 'Dakar', 'Bamako', 'Niamey', 'Ouagadougou'],
        'Population (M)': [1.2, 3.1, 2.4, 1.3, 2.2],
        'PIB/hab (USD)': [1850, 2400, 1200, 800, 1100],
        'Accès eau (%)': [45, 85, 60, 55, 70],
        'Accès électricité (%)': [42, 90, 65, 45, 75]
    }
    
    df_comparison = pd.DataFrame(cities_comparison)
    
    fig_comparison = px.scatter(
        df_comparison,
        x='PIB/hab (USD)',
        y='Accès eau (%)',
        size='Population (M)',
        color='Ville',
        title="Comparaison des Capitales Sahéliennes",
        hover_data=['Accès électricité (%)']
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)


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
                
                Vos domaines d'expertise incluent :
                - Planification urbaine et aménagement du territoire
                - Infrastructures urbaines (eau, électricité, transport, assainissement)
                - Habitat et logement social
                - Économie urbaine et développement local
                - Gouvernance urbaine et participation citoyenne
                - Résilience climatique et développement durable
                - Démographie urbaine et migration
                - Services urbains de base
                
                Répondez de manière professionnelle, avec des données concrètes quand possible, et proposez des solutions pratiques.
                """
                
                # CORRECTION ICI - Suppression du "full" en double
                full_prompt = f"{system_prompt}\n\nQuestion de l'utilisateur: {prompt}"
                
                response = generate_enhanced_content(full_prompt, clients, 600)
                st.markdown(response)
                
                # Ajout de la réponse à l'historique
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Suggestions de questions
    st.markdown("---")
    st.markdown("### 💡 Questions suggérées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Comment améliorer l'accès à l'eau potable ?"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment améliorer l'accès à l'eau potable dans une ville en croissance rapide ?"
            })
            st.rerun()
        
        if st.button("Stratégies de logement social"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Quelles sont les meilleures stratégies de logement social pour les villes africaines ?"
            })
            st.rerun()
        
        if st.button("Gestion des déchets urbains"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment mettre en place un système efficace de gestion des déchets urbains ?"
            })
            st.rerun()
    
    with col2:
        if st.button("Transport public durable"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment développer un système de transport public durable et abordable ?"
            })
            st.rerun()
        
        if st.button("Résilience climatique"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Comment renforcer la résilience climatique des villes sahéliennes ?"
            })
            st.rerun()
        
        if st.button("Financement de projets urbains"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Quelles sont les sources de financement pour les projets de développement urbain ?"
            })
            st.rerun()
    
    # Bouton pour effacer l'historique
    if st.button("🗑️ Effacer la conversation"):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Bonjour ! Je suis votre assistant IA spécialisé en développement urbain. Comment puis-je vous aider aujourd'hui ?"
            }
        ]
        st.rerun()
def resources_tab():
    """Onglet Ressources et Documentation"""
    st.markdown('<div class="main-header">📚 RESSOURCES ET DOCUMENTATION</div>', unsafe_allow_html=True)
    
    # Section Guides méthodologiques
    st.markdown('<div class="section-header">📖 Guides Méthodologiques</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🏗️ Diagnostic d'Infrastructure
        
        **Étapes clés :**
        1. **Inventaire des équipements existants**
           - Réseaux d'eau et d'assainissement
           - Infrastructures électriques
           - Réseau routier et transport
        
        2. **Évaluation de l'état technique**
           - Taux de couverture par service
           - Qualité et fiabilité des services
           - Capacité et besoins futurs
        
        3. **Analyse des déficits**
           - Zones non desservies
           - Surcharge des équipements
           - Vétusté des installations
        
        4. **Priorisation des interventions**
           - Urgence technique
           - Impact sur la population
           - Faisabilité financière
        """)
    
    with col2:
        st.markdown("""
        ### 🏠 Analyse de l'Habitat
        
        **Méthodologie :**
        1. **Typologie du parc de logements**
           - Matériaux de construction
           - Modes d'occupation
           - Densité d'occupation
        
        2. **Évaluation de la qualité**
           - Accès aux services de base
           - Salubrité et sécurité
           - Conformité aux normes
        
        3. **Cartographie des quartiers**
           - Habitat planifié vs informel
           - Zones à risque
           - Potentiel de densification
        
        4. **Besoins en logements**
           - Déficit quantitatif
           - Déficit qualitatif
           - Projections démographiques
        """)
    
    # Section Indicateurs de référence
    st.markdown('<div class="section-header">📊 Indicateurs de Référence</div>', unsafe_allow_html=True)
    
    # Tableau des indicateurs ODD 11
    st.markdown("### 🎯 Objectifs de Développement Durable - ODD 11")
    
    odd11_data = {
        'Indicateur': [
            '11.1.1 - Population en bidonvilles',
            '11.2.1 - Accès au transport public',
            '11.3.1 - Consommation foncière',
            '11.5.1 - Pertes dues aux catastrophes',
            '11.6.1 - Déchets municipaux collectés',
            '11.7.1 - Espaces verts publics'
        ],
        'Définition': [
            'Proportion de la population urbaine vivant dans des bidonvilles',
            'Proportion de la population ayant un accès pratique au transport public',
            'Ratio entre le taux de consommation foncière et le taux de croissance démographique',
            'Nombre de décès, personnes disparues et personnes directement touchées',
            'Proportion de déchets municipaux solides collectés et gérés',
            'Proportion moyenne d\'espaces verts publics dans les villes'
        ],
        'Objectif 2030': [
            '< 20%',
            '> 70%',
            '< 1.5',
            'Réduction significative',
            '> 80%',
            '> 15 m²/hab'
        ]
    }
    
    df_odd11 = pd.DataFrame(odd11_data)
    st.dataframe(df_odd11, use_container_width=True)
    
    # Section Outils et modèles
    st.markdown('<div class="section-header">🛠️ Outils et Modèles</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Modèles de questionnaires", "📈 Calculateurs", "🗺️ Outils cartographiques"])
    
    with tab1:
        st.markdown("""
        ### 📝 Questionnaires Types
        
        #### Enquête Ménages - Accès aux Services
        1. **Identification du ménage**
           - Localisation (quartier, rue)
           - Composition du ménage
           - Revenus et activités
        
        2. **Accès à l'eau**
           - Source principale d'approvisionnement
           - Distance/temps d'accès
           - Qualité perçue
           - Coût mensuel
        
        3. **Accès à l'électricité**
           - Type de raccordement
           - Fiabilité du service
           - Coût mensuel
           - Sources alternatives
        
        4. **Logement**
           - Type de construction
           - Nombre de pièces
           - Mode d'occupation
           - Équipements disponibles
        """)
        
        # Bouton de téléchargement du questionnaire
        questionnaire_content = """
        QUESTIONNAIRE DIAGNOSTIC URBAIN - ENQUÊTE MÉNAGES
        
        SECTION A - IDENTIFICATION
        A1. Quartier : ________________
        A2. Rue/Avenue : ________________
        A3. Nombre de personnes dans le ménage : ____
        A4. Revenus mensuels du ménage : ______ USD
        
        SECTION B - ACCÈS À L'EAU
        B1. Source principale d'eau potable :
        □ Robinet dans le logement
        □ Robinet dans la cour
        □ Borne fontaine publique
        □ Puits
        □ Autre : ________________
        
        B2. Temps pour aller chercher l'eau : ______ minutes
        B3. Coût mensuel de l'eau : ______ USD
        B4. Qualité de l'eau : □ Très bonne □ Bonne □ Moyenne □ Mauvaise
        
        SECTION C - ACCÈS À L'ÉLECTRICITÉ
        C1. Type de raccordement :
        □ Raccordement officiel
        □ Raccordement informel
        □ Pas de raccordement
        
        C2. Fréquence des coupures :
        □ Jamais □ Rarement □ Souvent □ Très souvent
        
        C3. Coût mensuel de l'électricité : ______ USD
        
        SECTION D - LOGEMENT
        D1. Type de construction :
        □ Béton/Dur □ Semi-dur □ Traditionnel □ Précaire
        
        D2. Nombre de pièces : ______
        D3. Mode d'occupation :
        □ Propriétaire □ Locataire □ Logé gratuitement
        
        D4. Équipements disponibles :
        □ Toilettes dans le logement
        □ Cuisine équipée
        □ Douche/salle de bain
        """
        
        st.download_button(
            label="📥 Télécharger le questionnaire complet",
            data=questionnaire_content,
            file_name="questionnaire_diagnostic_urbain.txt",
            mime="text/plain"
        )
    
    with tab2:
        st.markdown("### 🧮 Calculateurs Urbains")
        
        # Calculateur de densité
        st.markdown("#### Calculateur de Densité Urbaine")
        
        col1, col2 = st.columns(2)
        with col1:
            calc_population = st.number_input("Population", value=100000, step=1000, key="calc_pop")
            calc_area = st.number_input("Superficie (km²)", value=50.0, step=1.0, key="calc_area")
        
        with col2:
            if calc_area > 0:
                density = calc_population / calc_area
                st.metric("Densité (hab/km²)", f"{density:,.0f}")
                
                if density < 500:
                    st.success("Densité faible - Potentiel de densification")
                elif density < 2000:
                    st.info("Densité modérée - Équilibre acceptable")
                elif density < 5000:
                    st.warning("Densité élevée - Attention aux services")
                else:
                    st.error("Densité très élevée - Risque de surcharge")
        
        # Calculateur de besoins en logements
        st.markdown("#### Calculateur de Besoins en Logements")
        
        col1, col2 = st.columns(2)
        with col1:
            current_housing = st.number_input("Logements existants", value=20000, step=100)
            household_size = st.number_input("Taille moyenne des ménages", value=6.5, step=0.1)
            growth_rate_housing = st.number_input("Taux de croissance (%)", value=3.5, step=0.1)
        
        with col2:
            needed_housing = calc_population / household_size
            housing_deficit = max(0, needed_housing - current_housing)
            
            st.metric("Logements nécessaires", f"{needed_housing:,.0f}")
            st.metric("Déficit actuel", f"{housing_deficit:,.0f}")
            
            # Projection sur 10 ans
            future_population = calc_population * (1 + growth_rate_housing/100)**10
            future_housing_need = future_population / household_size
            additional_housing = future_housing_need - needed_housing
            
            st.metric("Besoins additionnels (10 ans)", f"{additional_housing:,.0f}")
    
    with tab3:
        st.markdown("""
        ### 🗺️ Outils Cartographiques Recommandés
        
        #### Logiciels SIG Open Source
        - **QGIS** : Système d'information géographique complet
        - **OpenStreetMap** : Cartographie collaborative
        - **PostGIS** : Extension spatiale pour PostgreSQL
        
        #### Données Géospatiales
        - **Sentinel Hub** : Images satellites gratuites
        - **Global Human Settlement Layer** : Données d'occupation du sol
        - **OpenStreetMap** : Données vectorielles urbaines
        
        #### Plateformes en ligne
        - **Google Earth Engine** : Analyse d'images satellites
        - **ArcGIS Online** : Cartographie web
        - **Mapbox** : Cartes interactives personnalisées
        
        #### Méthodologie de cartographie urbaine
        1. **Collecte des données de base**
           - Limites administratives
           - Réseau routier
           - Bâtiments et parcelles
        
        2. **Cartographie thématique**
           - Densité de population
           - Accès aux services
           - Types d'habitat
           - Risques naturels
        
        3. **Analyse spatiale**
           - Zones de couverture des services
           - Accessibilité et mobilité
           - Croissance urbaine
        """)
    
    # Section Bibliographie
    st.markdown('<div class="section-header">📚 Bibliographie et Références</div>', unsafe_allow_html=True)
    
    references = [
        {
            "titre": "UN-Habitat - World Cities Report 2022",
            "auteur": "Programme des Nations Unies pour les établissements humains",
            "annee": "2022",
            "description": "Rapport mondial sur l'état des villes et les tendances d'urbanisation"
        },
        {
            "titre": "African Development Bank - Africa's Urbanization Dynamics",
            "auteur": "Banque Africaine de Développement",
            "annee": "2021",
            "description": "Analyse des dynamiques d'urbanisation en Afrique"
        },
        {
            "titre": "Cities Alliance - City Development Strategies",
            "auteur": "Cities Alliance",
            "annee": "2020",
            "description": "Guide méthodologique pour les stratégies de développement urbain"
        },
        {
            "titre": "OECD - Urban Policy Reviews: Africa",
            "auteur": "Organisation de Coopération et de Développement Économiques",
            "annee": "2021",
            "description": "Revue des politiques urbaines en Afrique"
        }
    ]
    
    for ref in references:
        st.markdown(f"""
        **{ref['titre']}** ({ref['annee']})  
        *{ref['auteur']}*  
        {ref['description']}
        """)
        st.markdown("---")

def main():
    """Fonction principale de l'application"""
    
    # Header de l'application
    create_header()
    
    # Navigation par onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏙️ Diagnostic", 
        "📊 Dashboard", 
        "🤖 Assistant IA", 
        "📚 Ressources"
    ])
    
    with tab1:
        diagnostic_tab()
    
    with tab2:
        dashboard_tab()
    
    with tab3:
        chatbot_tab()
    
    with tab4:
        resources_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>AfricanCities IA Services</strong> - Centre of Urban Systems, UM6P</p>
        <p>Plateforme de diagnostic urbain intelligent pour les villes africaines</p>
        <p><em>Version 2.0 - Développé avec Streamlit et IA générative</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
