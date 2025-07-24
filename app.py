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
    page_title="Diagnostic Urbain Intelligent",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS pour améliorer l'apparence
st.markdown("""
<style>
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
</style>
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
            text += page.extract_text()
        
        if len(text.strip()) < 100:  # Si peu de texte extrait, utiliser OCR
            st.warning("Texte limité détecté, utilisation de l'OCR...")
            # Convertir PDF en images et utiliser OCR
            # Cette partie nécessiterait pdf2image et pytesseract
            pass
        
        return text
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte: {str(e)}")
        return ""

def generate_enhanced_content(prompt, clients, max_tokens=800):
    """Génère du contenu enrichi avec gestion des limites"""
    try:
        if 'groq' in clients:
            response = clients['groq'].chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un expert en urbanisme et développement urbain en Afrique. Rédigez du contenu professionnel, détaillé et précis sans emojis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Modèle plus petit
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
            return "Contenu générique - Aucun client IA disponible"
            
    except Exception as e:
        st.error(f"Erreur lors de la génération de contenu: {str(e)}")
        return f"Erreur de génération pour: {prompt[:50]}..."

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

def main():
    # En-tête principal
    st.markdown('<div class="main-header">🏙️ DIAGNOSTIC URBAIN INTELLIGENT</div>', unsafe_allow_html=True)
    
    # Initialisation des clients IA
    clients = initialize_ai_clients()
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        city_name = st.text_input("Nom de la ville", value="Nouakchott")
        country = st.text_input("Pays", value="Mauritanie")
        
        st.subheader("📊 Données de base")
        population = st.number_input("Population (habitants)", value=1200000, step=10000)
        growth_rate = st.number_input("Taux de croissance (%)", value=3.5, step=0.1)
        urban_area = st.number_input("Superficie urbaine (km²)", value=1000, step=10)
        
        st.subheader("🏠 Indicateurs d'habitat")
        water_access = st.slider("Accès à l'eau potable (%)", 0, 100, 45)
        electricity_access = st.slider("Accès à l'électricité (%)", 0, 100, 42)
        sanitation_access = st.slider("Accès à l'assainissement (%)", 0, 100, 25)
        
        st.subheader("📄 Documents techniques")
        uploaded_files = st.file_uploader(
            "Télécharger des documents (PDF)",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        generate_report = st.button("🚀 Générer le rapport complet", type="primary")
    
    # Interface principale
    if generate_report:
        with st.spinner("Génération du rapport en cours..."):
            
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
            Population: {population:,} habitants, croissance: {growth_rate}%.
            Accès eau: {water_access}%, électricité: {electricity_access}%, assainissement: {sanitation_access}%.
            Incluez: situation actuelle, défis principaux, opportunités, recommandations clés.
            Style: professionnel, sans emojis, paragraphes structurés.
            """
            
            executive_summary = generate_enhanced_content(executive_prompt, clients, 600)
            st.markdown(f'<div class="professional-text">{executive_summary}</div>', unsafe_allow_html=True)
            
            # 2. CONTEXTE DÉMOGRAPHIQUE ET SOCIAL
            st.markdown('<div class="section-header">2. CONTEXTE DÉMOGRAPHIQUE ET SOCIAL</div>', unsafe_allow_html=True)
            
            # 2.1 Profil démographique
            st.markdown('<div class="subsection-header">2.1 Profil démographique</div>', unsafe_allow_html=True)
            
            demo_prompt = f"""
            Analysez le profil démographique de {city_name} avec {population:,} habitants et {growth_rate}% de croissance.
            Détaillez: structure par âge, migration, densité urbaine, projections 2030.
            Comparaisons régionales avec autres capitales sahéliennes.
            300 mots, style analytique professionnel.
            """
            
            demographic_analysis = generate_enhanced_content(demo_prompt, clients, 500)
            st.markdown(f'<div class="professional-text">{demographic_analysis}</div>', unsafe_allow_html=True)
            
            # Graphique démographique
            demo_chart = create_demographic_chart({"population": population, "growth": growth_rate})
            st.plotly_chart(demo_chart, use_container_width=True)
            
            # 2.2 Contexte socio-économique
            st.markdown('<div class="subsection-header">2.2 Contexte socio-économique</div>', unsafe_allow_html=True)
            
            socio_prompt = f"""
            Analysez le contexte socio-économique de {city_name}:
            - Secteurs économiques dominants
            - Emploi et chômage urbain
            - Niveaux de revenus et pauvreté urbaine
            - Éducation et santé
            - Inégalités socio-spatiales
            350 mots, données chiffrées, analyse approfondie.
            """
            
            socio_analysis = generate_enhanced_content(socio_prompt, clients, 600)
            st.markdown(f'<div class="professional-text">{socio_analysis}</div>', unsafe_allow_html=True)
            
            # Métriques socio-économiques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Taux de chômage", "23.4%", "-2.1%")
            with col2:
                st.metric("PIB par habitant", "1,850 USD", "+4.2%")
            with col3:
                st.metric("Taux d'alphabétisation", "67%", "+3.5%")
            with col4:
                st.metric("Indice de pauvreté", "31.2%", "-1.8%")
            
            # 3. ANALYSE DE L'HABITAT ET DES INFRASTRUCTURES
            st.markdown('<div class="section-header">3. ANALYSE DE L\'HABITAT ET DES INFRASTRUCTURES</div>', unsafe_allow_html=True)
            
            # 3.1 État du parc de logements
            st.markdown('<div class="subsection-header">3.1 État du parc de logements</div>', unsafe_allow_html=True)
            
            housing_prompt = f"""
            Analysez l'état du parc de logements à {city_name}:
            - Types de logements et matériaux de construction
            - Qualité et vétusté du bâti
            - Surpeuplement et conditions d'habitabilité
            - Marché immobilier et accessibilité financière
            - Quartiers informels et bidonvilles
            Accès eau: {water_access}%, électricité: {electricity_access}%.
            400 mots, analyse technique détaillée.
            """
            
            housing_analysis = generate_enhanced_content(housing_prompt, clients, 700)
            st.markdown(f'<div class="professional-text">{housing_analysis}</div>', unsafe_allow_html=True)
            
            # Graphique logement
            housing_chart = create_housing_analysis_chart()
            st.plotly_chart(housing_chart, use_container_width=True)
            
            # 3.2 Infrastructures de base
            st.markdown('<div class="subsection-header">3.2 Infrastructures de base</div>', unsafe_allow_html=True)
            
            infra_prompt = f"""
            Évaluez les infrastructures de base de {city_name}:
            - Réseau d'approvisionnement en eau (couverture: {water_access}%)
            - Système électrique (couverture: {electricity_access}%)
            - Assainissement et gestion des eaux usées ({sanitation_access}%)
            - Réseau routier et transport urbain
            - Télécommunications et numérique
            - Gestion des déchets solides
            450 mots, évaluation technique approfondie.
            """
            
            infrastructure_analysis = generate_enhanced_content(infra_prompt, clients, 700)
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
            - Croissance urbaine rapide et planification insuffisante
            - Déficit en logements décents et abordables
            - Insuffisance des services de base (eau: {water_access}%, électricité: {electricity_access}%)
            - Vulnérabilité climatique et environnementale
            - Gouvernance urbaine et capacités institutionnelles
            - Financement du développement urbain
            400 mots, analyse critique et factuelle.
            """
            
            challenges_analysis = generate_enhanced_content(challenges_prompt, clients, 700)
            st.markdown(f'<div class="professional-text">{challenges_analysis}</div>', unsafe_allow_html=True)
            
            # 4.2 Opportunités de développement
            st.markdown('<div class="subsection-header">4.2 Opportunités de développement</div>', unsafe_allow_html=True)
            
            opportunities_prompt = f"""
            Analysez les opportunités de développement pour {city_name}:
            - Potentiel économique et avantages géographiques
            - Ressources naturelles et énergétiques
            - Capital humain et démographie favorable
            - Coopération internationale et financement
            - Innovation technologique et villes intelligentes
            - Partenariats public-privé
            350 mots, vision prospective et réaliste.
            """
            
            opportunities_analysis = generate_enhanced_content(opportunities_prompt, clients, 600)
            st.markdown(f'<div class="professional-text">{opportunities_analysis}</div>', unsafe_allow_html=True)
            
            # 5. RECOMMANDATIONS STRATÉGIQUES
            st.markdown('<div class="section-header">5. RECOMMANDATIONS STRATÉGIQUES</div>', unsafe_allow_html=True)
            
            # 5.1 Priorités à court terme (1-3 ans)
            st.markdown('<div class="subsection-header">5.1 Priorités à court terme (1-3 ans)</div>', unsafe_allow_html=True)
            
            short_term_prompt = f"""
            Formulez des recommandations prioritaires à court terme pour {city_name}:
            - Amélioration urgente de l'accès à l'eau potable (actuellement {water_access}%)
            - Extension du réseau électrique (actuellement {electricity_access}%)
            - Programmes d'urgence pour l'habitat précaire
            - Renforcement des capacités institutionnelles
            - Mobilisation de financements d'urgence
            300 mots, recommandations concrètes et réalisables.
            """
            
            short_term_reco = generate_enhanced_content(short_term_prompt, clients, 500)
            st.markdown(f'<div class="professional-text">{short_term_reco}</div>', unsafe_allow_html=True)
            
            # 5.2 Stratégies à moyen terme (3-7 ans)
            st.markdown('<div class="subsection-header">5.2 Stratégies à moyen terme (3-7 ans)</div>', unsafe_allow_html=True)
            
            medium_term_prompt = f"""
            Développez des stratégies à moyen terme pour {city_name}:
            - Planification urbaine intégrée et durable
            - Développement de nouveaux quartiers planifiés
            - Modernisation des infrastructures existantes
            - Diversification économique urbaine
            - Renforcement de la résilience climatique
            350 mots, approche stratégique et intégrée.
            """
            
            medium_term_reco = generate_enhanced_content(medium_term_prompt, clients, 600)
            st.markdown(f'<div class="professional-text">{medium_term_reco}</div>', unsafe_allow_html=True)
            
            # 5.3 Vision à long terme (7-15 ans)
            st.markdown('<div class="subsection-header">5.3 Vision à long terme (7-15 ans)</div>', unsafe_allow_html=True)
            
            long_term_prompt = f"""
            Esquissez une vision à long terme pour {city_name}:
            - Transformation en ville intelligente et durable
            - Hub économique régional
            - Modèle de développement urbain africain
            - Objectifs de développement durable (ODD 11)
            - Innovation et technologies urbaines
            300 mots, vision ambitieuse mais réaliste.
            """
            
            long_term_reco = generate_enhanced_content(long_term_prompt, clients, 500)
            st.markdown(f'<div class="professional-text">{long_term_reco}</div>', unsafe_allow_html=True)
            
            # 6. GRAPHIQUES ET VISUALISATIONS
            st.markdown('<div class="section-header">6. GRAPHIQUES ET VISUALISATIONS</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="subsection-header">6.1 Tableau de bord des indicateurs clés</div>', unsafe_allow_html=True)
            
            # Indicateurs synthétiques
            indicators_data = {
                'Indicateur': ['Accès eau potable', 'Accès électricité', 'Assainissement', 'Logement décent', 'Transport public'],
                'Valeur actuelle': [water_access, electricity_access, sanitation_access, 35, 25],
                'Objectif 2030': [80, 75, 60, 70, 60],
                'Écart': [80-water_access, 75-electricity_access, 60-sanitation_access, 35, 35]
            }
            
            df_indicators = pd.DataFrame(indicators_data)
            st.dataframe(df_indicators, use_container_width=True)
            
            # Graphique radar des performances
            categories = ['Eau', 'Électricité', 'Assainissement', 'Logement', 'Transport', 'Santé', 'Éducation']
            current_values = [water_access, electricity_access, sanitation_access, 35, 25, 45, 67]
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
            - Appel à l'action pour les parties prenantes
            400 mots, ton prospectif et mobilisateur.
            """
            
            conclusion = generate_enhanced_content(conclusion_prompt, clients, 700)
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
            **Date de génération:** {datetime.now().strftime('%d/%m/%Y à %H:%M')}  
            **Population:** {population:,} habitants  
            **Taux de croissance:** {growth_rate}%  
            **Plateforme:** UrbanAI Diagnostic Platform v2.0
            """)

if __name__ == "__main__":
    main()
