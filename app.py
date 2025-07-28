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
    
    .web-info-box {
        background-color: #e8f4fd;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #17a2b8;
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

def get_wikipedia_info(city_name, country_name, lang="fr"):
    """Récupère des informations sur la ville depuis Wikipedia"""
    try:
        wikipedia.set_lang(lang)
        
        # Essayer différentes variantes du nom de la ville
        search_terms = [
            f"{city_name}",
            f"{city_name} {country_name}",
            f"{city_name}, {country_name}"
        ]
        
        for term in search_terms:
            try:
                # Rechercher la page
                page_title = wikipedia.search(term, results=1)
                if page_title:
                    page = wikipedia.page(page_title[0])
                    summary = wikipedia.summary(term, sentences=5)
                    
                    return {
                        'title': page.title,
                        'summary': summary,
                        'url': page.url,
                        'found': True
                    }
            except wikipedia.exceptions.DisambiguationError as e:
                # Prendre la première option en cas d'ambiguïté
                try:
                    page = wikipedia.page(e.options[0])
                    summary = wikipedia.summary(e.options[0], sentences=5)
                    return {
                        'title': page.title,
                        'summary': summary,
                        'url': page.url,
                        'found': True
                    }
                except:
                    continue
            except:
                continue
        
        # Si aucune information trouvée en français, essayer en anglais
        if lang == "fr":
            return get_wikipedia_info(city_name, country_name, lang="en")
        
        return {
            'title': f"{city_name}",
            'summary': f"Aucune information Wikipedia trouvée pour {city_name}, {country_name}.",
            'url': None,
            'found': False
        }
        
    except Exception as e:
        return {
            'title': f"{city_name}",
            'summary': f"Erreur lors de la recherche d'informations sur {city_name}: {str(e)}",
            'url': None,
            'found': False
        }

def get_web_urban_data(city_name, country_name):
    """Collecte des données urbaines depuis différentes sources web"""
    web_data = {
        'wikipedia_info': get_wikipedia_info(city_name, country_name),
        'additional_context': f"Recherche web effectuée pour {city_name}, {country_name}"
    }
    
    # Ici, tu peux ajouter d'autres sources de données web
    # Par exemple : World Bank API, UN Data, etc.
    
    return web_data

def format_web_info_for_prompt(web_data):
    """Formate les informations web pour inclusion dans le prompt"""
    if not web_data:
        return ""
    
    formatted_info = "\n\n=== INFORMATIONS WEB COLLECTÉES ===\n"
    
    # Informations Wikipedia
    wiki_info = web_data.get('wikipedia_info', {})
    if wiki_info.get('found', False):
        formatted_info += f"\n--- Wikipedia: {wiki_info.get('title', 'N/A')} ---\n"
        formatted_info += wiki_info.get('summary', 'Aucun résumé disponible')
        if wiki_info.get('url'):
            formatted_info += f"\nSource: {wiki_info.get('url')}"
    else:
        formatted_info += f"\n--- Wikipedia ---\n{wiki_info.get('summary', 'Aucune information trouvée')}"
    
    formatted_info += "\n\n=== FIN DES INFORMATIONS WEB ===\n"
    
    return formatted_info

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

def generate_enhanced_content_with_docs_and_web(prompt, clients, documents_content=None, web_data=None, max_tokens=800, include_Web_Search=False):
    """Génère du contenu enrichi en incluant les documents uploadés ET les données web"""
    try:
        # Construire le prompt avec les documents et les données web
        enhanced_prompt = prompt
        
        # Ajouter les informations web
        if web_data:
            web_info = format_web_info_for_prompt(web_data)
            enhanced_prompt = prompt + web_info
        
        # Recherche web si nécessaire
        if include_Web_Search:
            search_query = prompt.split(":")[-1].strip() if ":" in prompt else prompt
            web_results = search_web_info(search_query)
            
            if web_results:
                web_context = "\n".join([f"- {result['snippet']} (Source: {result['url']})" for result in web_results])
                enhanced_prompt += f"\n\nInformations web récentes:\n{web_context}"
        
        # Ajouter les documents si disponibles
        if documents_content and len(documents_content) > 0:
            docs_text = "\n\nDOCUMENTS TECHNIQUES FOURNIS :\n"
            for i, doc in enumerate(documents_content, 1):
                docs_text += f"\n--- Document {i}: {doc['filename']} ---\n"
                docs_text += doc['content'][:2000]  # Limiter chaque document à 2000 caractères
                docs_text += "\n"
            
            enhanced_prompt += docs_text + "\n\nVeuillez intégrer les informations de ces documents techniques ET les données web dans votre analyse."
        elif web_data:
            enhanced_prompt += "\n\nVeuillez intégrer les informations web collectées dans votre analyse."
        
        if 'groq' in clients:
            response = clients['groq'].chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Analysez les documents fournis et les informations web collectées, puis intégrez-les dans vos réponses. Rédigez du contenu professionnel, détaillé et précis sans emojis. Citez vos sources quand vous utilisez des informations externes. Si vous ne connaissez pas une information précise, dites 'Je ne connais pas cette information spécifique'. Gardez vos réponses courtes et précises (max 150 mots pour le chatbot)."
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
            content = response.choices[0].message.content
            
            # Ajouter la source si recherche web
            if include_Web_Search and web_results:
                content += f"\n\n📍 *Sources web consultées: {', '.join([r['url'] for r in web_results])}"
            
            return content
        
        elif 'openai' in clients:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Analysez les documents fournis et les informations web collectées, puis intégrez-les dans vos réponses. Rédigez du contenu professionnel, détaillé et précis sans emojis. Citez vos sources quand vous utilisez des informations externes. Si vous ne connaissez pas une information précise, dites 'Je ne connais pas cette information spécifique'. Gardez vos réponses courtes et précises (max 150 mots pour le chatbot)."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            content = response.choices[0].message.content
            
            if include_Web_Search and web_results:
                content += f"\n\n📍 *Sources web consultées: {', '.join([r['url'] for r in web_results])}"
            
            return content
        
        else:
            return "Contenu générique - Aucun client IA disponible"
            
    except Exception as e:
        st.error(f"Erreur lors de la génération de contenu: {str(e)}")
        return f"Erreur de génération pour: {prompt[:50]}..."

def generate_enhanced_content_with_docs(prompt, clients, documents_content=None, max_tokens=800):
    """Génère du contenu enrichi avec gestion des limites (fonction de compatibilité)"""
    return generate_enhanced_content_with_docs_and_web(prompt, clients, documents_content, None, max_tokens)

def generate_enhanced_content(prompt, clients, max_tokens=800):
    """Génère du contenu enrichi avec gestion des limites (fonction de compatibilité)"""
    return generate_enhanced_content_with_docs_and_web(prompt, clients, None, None, max_tokens)

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
                    needs_Web_Search = any(word in prompt.lower() for word in ['récent', 'dernier', 'nouveau', 'actuel', '2024', '2025'])
                    
                    full_prompt = f"""
                    {system_prompt}
                    
                    Question de l'utilisateur : {prompt}
                    
                    Contexte : Nous travaillons sur un diagnostic urbain pour des villes africaines, notamment Nouakchott en Mauritanie.
                    
                    Répondez de manière concise et pratique. Si vous ne connaissez pas une information précise, dites-le clairement.
                    """
                    
                    response = generate_enhanced_content_with_docs_and_web(full_prompt, clients, None, None, 200, include_Web_Search=needs_Web_Search)
                
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
        
        # Option pour activer la recherche web
        enable_Web_Search = st.checkbox("🌐 Enrichir avec des données web", value=True, help="Collecte automatiquement des informations sur la ville depuis Wikipedia et autres sources")
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
            
            # Collecte des données web si activée
            web_data = None
            if enable_Web_Search:
                with st.spinner("🌐 Collecte des données web en cours..."):
                    web_data = get_web_urban_data(city_name, country)
                    
                    # Afficher les informations web collectées
                    if web_data and web_data.get('wikipedia_info', {}).get('found', False):
                        wiki_info = web_data['wikipedia_info']
                        st.markdown(f"""
                        <div class="web-info-box">
                            <h4>🌐 Informations Web Collectées</h4>
                            <p><strong>Source Wikipedia:</strong> {wiki_info.get('title', 'N/A')}</p>
                            <p>{wiki_info.get('summary', 'Aucun résumé disponible')[:200]}...</p>
                            {f'<p><a href="{wiki_info.get("url")}" target="_blank">Voir la page complète</a></p>' if wiki_info.get('url') else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("🌐 Recherche web effectuée - Informations limitées trouvées")
            
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
            web_status = "✅ Activée" if enable_Web_Search else "❌ Désactivée"
            st.info(f"""
            **Diagnostic configuré pour:** {city_name}, {country}  
            **Type:** {diagnostic_type}  
            **Population:** {population:,} habitants  
            **Date:** {diagnostic_date.strftime('%d/%m/%Y')}  
            **Recherche web:** {web_status}  
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
            
            executive_summary = generate_enhanced_content_with_docs_and_web(executive_prompt, clients, documents_content, web_data, 600)
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
            
            demographic_analysis = generate_enhanced_content_with_docs_and_web(demo_prompt, clients, documents_content, web_data, 500)
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
            
            socio_analysis = generate_enhanced_content_with_docs_and_web(socio_prompt, clients, documents_content, web_data, 600)
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
            
            housing_analysis = generate_enhanced_content_with_docs_and_web(housing_prompt, clients, documents_content, web_data, 700)
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
            
            infrastructure_analysis = generate_enhanced_content_with_docs_and_web(infra_prompt, clients, documents_content, web_data, 700)
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
            
            challenges_analysis = generate_enhanced_content_with_docs_and_web(challenges_prompt, clients, documents_content, web_data, 700)
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
            
            opportunities_analysis = generate_enhanced_content_with_docs_and_web(opportunities_prompt, clients, documents_content, web_data, 600)
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
            
            short_term_reco = generate_enhanced_content_with_docs_and_web(short_term_prompt, clients, documents_content, web_data, 500)
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
            
            medium_term_reco = generate_enhanced_content_with_docs_and_web(medium_term_prompt, clients, documents_content, web_data, 600)
            st.markdown(f'<div class="professional-text">{medium_term_reco}</div>', unsafe_allow_html=True)
            
            # 5.3 Vision à long terme (7-15 ans)
            st.markdown('<div class="subsection-header">5.3 Vision à long terme (7-15 ans)</div>', unsafe_allow_html=True)
            
           long_term_prompt = f"""
            Esquissez une vision à long terme pour {city_name}:
           - Transformation en ville intelligente et durable
           - Hub économique régional basé sur {', '.join(main_sectors) if main_sectors else 'les secteurs porteurs'}
           - Inclusion sociale et égalité d'accès aux services
           - Adaptation au changement climatique et neutralité carbone
           - Gouvernance participative et innovation numérique
           300 mots, style prospectif et inspirant.
           """
            
            long_term_reco = generate_enhanced_content_with_docs_and_web(long_term_prompt, clients, documents_content, web_data, 500)
            st.markdown(f'<div class="professional-text">{long_term_reco}</div>', unsafe_allow_html=True)
            
            # 6. GRAPHIQUES ET VISUALISATIONS
            st.markdown('<div class="section-header">6. GRAPHIQUES ET VISUALISATIONS</div>', unsafe_allow_html=True)
            st.info("Les graphiques interactifs sont présentés ci-dessus dans chaque section thématique. Vous pouvez les exporter au format image ou PDF.")
            
            # 7. CONCLUSION PROSPECTIVE
            st.markdown('<div class="section-header">7. CONCLUSION PROSPECTIVE</div>', unsafe_allow_html=True)
            conclusion_prompt = f"""
            Rédigez une conclusion prospective pour le diagnostic urbain de {city_name}, en insistant sur l'importance d'une approche intégrée, la mobilisation des acteurs locaux, et l'innovation pour relever les défis urbains du XXIe siècle. 200 mots, ton mobilisateur.
            """
            conclusion = generate_enhanced_content_with_docs_and_web(conclusion_prompt, clients, documents_content, web_data, 350)
            st.markdown(f'<div class="professional-text">{conclusion}</div>', unsafe_allow_html=True)
            
            # Génération du rapport PDF
            st.markdown("---")
            st.subheader("📥 Télécharger le rapport PDF professionnel")
            report_data = {
                "executive_summary": executive_summary,
                "demographic_context": demographic_analysis + "\n\n" + socio_analysis,
                "housing_analysis": housing_analysis + "\n\n" + infrastructure_analysis,
                "challenges": challenges_analysis + "\n\n" + opportunities_analysis,
                "recommendations": short_term_reco + "\n\n" + medium_term_reco + "\n\n" + long_term_reco,
                "conclusion": conclusion
            }
            charts_data = {
                "demographic_chart": demo_chart,
                "housing_chart": housing_chart,
                "infra_chart": infra_chart
            }
            pdf_buffer = generate_professional_pdf_report(city_name, report_data, charts_data)
            st.download_button(
                label="📄 Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name=f"Diagnostic_{city_name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        st.success("✅ Rapport généré avec succès !")
    else:
        st.info("Remplissez le formulaire à gauche puis cliquez sur 'Générer le rapport complet' pour lancer le diagnostic urbain.")

def main():
    create_header()
    tabs = st.tabs(["🏙️ Diagnostic", "🤖 Chatbot"])
    with tabs[0]:
        diagnostic_tab()
    with tabs[1]:
        chatbot_tab()

if __name__ == "__main__":
    main()
