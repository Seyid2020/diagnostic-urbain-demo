

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import PyPDF2
import docx
import openai
import os
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# Configuration de la page
st.set_page_config(
    page_title="Diagnostic Urbain Intelligent",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .tab-description {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 5px solid #2a5298;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    }
    
    .form-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 16px rgba(40, 167, 69, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
    }
    
    .indicator-row {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #28a745;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la base de données
@st.cache_resource
def init_database():
    conn = sqlite3.connect('urban_diagnostic.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Table des indicateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            name TEXT,
            category TEXT,
            value REAL,
            unit TEXT,
            source TEXT,
            year INTEGER,
            city TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des diagnostics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnostics (
            id INTEGER PRIMARY KEY,
            city TEXT,
            country TEXT,
            region TEXT,
            population INTEGER,
            diagnostic_type TEXT,
            objective TEXT,
            target_audience TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'draft',
            pdf_path TEXT
        )
    ''')
    
    # Table des documents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            diagnostic_id INTEGER,
            filename TEXT,
            file_type TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (diagnostic_id) REFERENCES diagnostics (id)
        )
    ''')
    
    conn.commit()
    return conn

# Indicateurs complets par dimension
INDICATORS = {
    "Société": [
        {"code": "SP.POP.TOTL", "name": "Population totale", "unit": "habitants", "wb_available": True},
        {"code": "SP.POP.GROW", "name": "Taux de croissance démographique", "unit": "%", "wb_available": True},
        {"code": "SE.ADT.LITR.ZS", "name": "Taux d'alphabétisation des adultes", "unit": "%", "wb_available": True},
        {"code": "SH.STA.MORT", "name": "Taux de mortalité infantile", "unit": "‰", "wb_available": True},
        {"code": "SP.DYN.LE00.IN", "name": "Espérance de vie à la naissance", "unit": "années", "wb_available": True},
        {"code": "SE.PRM.NENR", "name": "Taux de scolarisation primaire", "unit": "%", "wb_available": True},
        {"code": "SH.MED.BEDS.ZS", "name": "Lits d'hôpital pour 1000 habitants", "unit": "pour 1000 hab", "wb_available": True},
    ],
    "Logement": [
        {"code": "SH.H2O.BASW.ZS", "name": "Accès à l'eau potable", "unit": "%", "wb_available": True},
        {"code": "SH.STA.BASS.ZS", "name": "Accès à l'assainissement", "unit": "%", "wb_available": True},
        {"code": "EG.ELC.ACCS.ZS", "name": "Accès à l'électricité", "unit": "%", "wb_available": True},
        {"code": "HOUSING_DENSITY", "name": "Densité de logement", "unit": "log/km²", "wb_available": False},
        {"code": "INFORMAL_SETTLEMENTS", "name": "Pourcentage d'habitats précaires", "unit": "%", "wb_available": False},
        {"code": "HOUSING_COST", "name": "Coût du logement/revenu", "unit": "%", "wb_available": False},
        {"code": "OVERCROWDING", "name": "Surpeuplement des logements", "unit": "%", "wb_available": False},
    ],
    "Développement Spatial": [
        {"code": "AG.LND.TOTL.K2", "name": "Superficie totale", "unit": "km²", "wb_available": True},
        {"code": "EN.POP.DNST", "name": "Densité de population", "unit": "hab/km²", "wb_available": True},
        {"code": "URBAN_SPRAWL", "name": "Indice d'étalement urbain", "unit": "index", "wb_available": False},
        {"code": "GREEN_SPACE", "name": "Espaces verts par habitant", "unit": "m²/hab", "wb_available": False},
        {"code": "LAND_USE_MIX", "name": "Mixité fonctionnelle", "unit": "index", "wb_available": False},
        {"code": "URBAN_PLANNING", "name": "Couverture planification urbaine", "unit": "%", "wb_available": False},
    ],
    "Infrastructure": [
        {"code": "IS.ROD.PAVE.ZS", "name": "Routes pavées", "unit": "%", "wb_available": True},
        {"code": "IT.NET.USER.ZS", "name": "Utilisateurs d'Internet", "unit": "%", "wb_available": True},
        {"code": "IT.CEL.SETS.P2", "name": "Abonnements téléphoniques mobiles", "unit": "pour 100 hab", "wb_available": True},
        {"code": "TRANSPORT_ACCESS", "name": "Accès aux transports publics", "unit": "%", "wb_available": False},
        {"code": "WASTE_COLLECTION", "name": "Collecte des déchets", "unit": "%", "wb_available": False},
        {"code": "ENERGY_RELIABILITY", "name": "Fiabilité de l'approvisionnement énergétique", "unit": "%", "wb_available": False},
    ],
    "Environnement": [
        {"code": "EN.ATM.PM25.MC.M3", "name": "Pollution de l'air (PM2.5)", "unit": "μg/m³", "wb_available": True},
        {"code": "ER.H2O.FWTL.K3", "name": "Ressources en eau douce", "unit": "milliards m³", "wb_available": True},
        {"code": "AG.LND.FRST.ZS", "name": "Superficie forestière", "unit": "% du territoire", "wb_available": True},
        {"code": "FLOOD_RISK", "name": "Risque d'inondation", "unit": "index", "wb_available": False},
        {"code": "CLIMATE_VULNERABILITY", "name": "Vulnérabilité climatique", "unit": "index", "wb_available": False},
        {"code": "WASTE_RECYCLING", "name": "Taux de recyclage", "unit": "%", "wb_available": False},
    ],
    "Gouvernance": [
        {"code": "CC.GOV.WS.EST", "name": "Efficacité gouvernementale", "unit": "index", "wb_available": True},
        {"code": "RL.EST", "name": "État de droit", "unit": "index", "wb_available": True},
        {"code": "CC.EST", "name": "Contrôle de la corruption", "unit": "index", "wb_available": True},
        {"code": "CITIZEN_PARTICIPATION", "name": "Participation citoyenne", "unit": "%", "wb_available": False},
        {"code": "TRANSPARENCY_INDEX", "name": "Indice de transparence", "unit": "index", "wb_available": False},
        {"code": "PUBLIC_SERVICES", "name": "Qualité des services publics", "unit": "index", "wb_available": False},
    ],
    "Économie": [
        {"code": "NY.GDP.PCAP.CD", "name": "PIB par habitant", "unit": "USD", "wb_available": True},
        {"code": "SL.UEM.TOTL.ZS", "name": "Taux de chômage", "unit": "%", "wb_available": True},
        {"code": "SI.POV.NAHC", "name": "Taux de pauvreté", "unit": "%", "wb_available": True},
        {"code": "NE.GDI.TOTL.ZS", "name": "Formation brute de capital", "unit": "% du PIB", "wb_available": True},
        {"code": "INFORMAL_ECONOMY", "name": "Économie informelle", "unit": "% du PIB", "wb_available": False},
        {"code": "BUSINESS_ENVIRONMENT", "name": "Facilité de faire des affaires", "unit": "rang", "wb_available": False},
    ]
}

# Fonction de collecte automatique des données
def collect_worldbank_data(country_code, indicators, start_year=2018, end_year=2023):
    """Collecte les données de la Banque Mondiale avec gestion d'erreurs robuste"""
    collected_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_indicators = sum(len(indicator_list) for indicator_list in indicators.values())
    current_indicator = 0
    
    for category, indicator_list in indicators.items():
        collected_data[category] = {}
        status_text.text(f"Collecte en cours: {category}")
        
        for indicator in indicator_list:
            current_indicator += 1
            progress_bar.progress(current_indicator / total_indicators)
            
            try:
                if indicator.get('wb_available', False):
                    # Tentative de collecte via API Banque Mondiale
                    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator['code']}"
                    params = {
                        'date': f'{start_year}:{end_year}',
                        'format': 'json',
                        'per_page': 100
                    }
                    
                    response = requests.get(url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            # Chercher la valeur la plus récente
                            for entry in data[1]:
                                if entry['value'] is not None:
                                    collected_data[category][indicator['code']] = {
                                        'name': indicator['name'],
                                        'value': float(entry['value']),
                                        'unit': indicator['unit'],
                                        'year': int(entry['date']),
                                        'source': 'Banque Mondiale',
                                        'wb_available': True
                                    }
                                    break
                            else:
                                # Aucune valeur trouvée
                                collected_data[category][indicator['code']] = {
                                    'name': indicator['name'],
                                    'value': np.nan,
                                    'unit': indicator['unit'],
                                    'year': None,
                                    'source': 'Banque Mondiale - Pas de données',
                                    'wb_available': True
                                }
                        else:
                            collected_data[category][indicator['code']] = {
                                'name': indicator['name'],
                                'value': np.nan,
                                'unit': indicator['unit'],
                                'year': None,
                                'source': 'Banque Mondiale - Pas de données',
                                'wb_available': True
                            }
                    else:
                        collected_data[category][indicator['code']] = {
                            'name': indicator['name'],
                            'value': np.nan,
                            'unit': indicator['unit'],
                            'year': None,
                            'source': f'Erreur API ({response.status_code})',
                            'wb_available': True
                        }
                else:
                    # Indicateur non disponible via Banque Mondiale
                    collected_data[category][indicator['code']] = {
                        'name': indicator['name'],
                        'value': np.nan,
                        'unit': indicator['unit'],
                        'year': None,
                        'source': 'Saisie manuelle requise',
                        'wb_available': False
                    }
                    
            except Exception as e:
                collected_data[category][indicator['code']] = {
                    'name': indicator['name'],
                    'value': np.nan,
                    'unit': indicator['unit'],
                    'year': None,
                    'source': f'Erreur: {str(e)[:50]}...',
                    'wb_available': indicator.get('wb_available', False)
                }
    
    progress_bar.empty()
    status_text.empty()
    return collected_data

# Fonction de traitement des documents uploadés
def process_uploaded_documents(uploaded_files):
    """Traite les documents uploadés et extrait le contenu"""
    processed_docs = []
    
    for uploaded_file in uploaded_files:
        try:
            file_content = ""
            file_type = uploaded_file.type
            
            if file_type == "application/pdf":
                # Traitement PDF
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    file_content += page.extract_text() + "\n"
                    
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                # Traitement DOCX
                doc = docx.Document(uploaded_file)
                for paragraph in doc.paragraphs:
                    file_content += paragraph.text + "\n"
                    
            elif file_type in ["text/csv", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                # Traitement CSV/Excel
                if file_type == "text/csv":
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                file_content = df.to_string()
            
            processed_docs.append({
                'filename': uploaded_file.name,
                'type': file_type,
                'content': file_content,
                'size': len(file_content)
            })
            
        except Exception as e:
            st.error(f"Erreur lors du traitement de {uploaded_file.name}: {str(e)}")
    
    return processed_docs

# Fonction RAG pour recherche dans les documents
@st.cache_resource
def init_rag_system():
    """Initialise le système RAG"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except:
        return None

def search_in_documents(query, documents, model=None):
    """Recherche dans les documents avec RAG"""
    if not documents or not model:
        return []
    
    try:
        # Diviser les documents en chunks
        chunks = []
        chunk_metadata = []
        
        for doc in documents:
            content = doc['content']
            # Diviser en paragraphes
            paragraphs = content.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) > 50:  # Ignorer les paragraphes trop courts
                    chunks.append(paragraph.strip())
                    chunk_metadata.append({
                        'filename': doc['filename'],
                        'chunk_id': i,
                        'type': doc['type']
                    })
        
        if not chunks:
            return []
        
        # Encoder les chunks et la requête
        chunk_embeddings = model.encode(chunks)
        query_embedding = model.encode([query])
        
        # Recherche de similarité
        similarities = np.dot(chunk_embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 résultats
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.3:  # Seuil de similarité
                results.append({
                    'content': chunks[idx],
                    'metadata': chunk_metadata[idx],
                    'similarity': similarities[idx]
                })
        
        return results
        
    except Exception as e:
        st.error(f"Erreur dans la recherche RAG: {str(e)}")
        return []

# Fonction de génération du rapport PDF avancé
def generate_advanced_pdf_report(city_data, indicators_data, diagnostic_info, documents_info=None):
    """Génère un rapport PDF professionnel avec graphiques intégrés"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    
    # Styles personnalisés
    styles = getSampleStyleSheet()
    
    # Style titre principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3c72'),
        fontName='Helvetica-Bold'
    )
    
    # Style sous-titre
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2a5298'),
        fontName='Helvetica'
    )
    
    # Style section
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.HexColor('#2a5298'),
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#2a5298'),
        borderPadding=5,
        backColor=colors.HexColor('#f8f9fa')
    )
    
    # Style texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    story = []
    
    # Page de couverture
    story.append(Spacer(1, 50))
    story.append(Paragraph("DIAGNOSTIC URBAIN INTELLIGENT", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Ville de {city_data.get('city', 'N/A')}", subtitle_style))
    story.append(Paragraph(f"{city_data.get('country', 'N/A')}", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Informations générales
    info_data = [
        ['Région:', city_data.get('region', 'N/A')],
        ['Population:', f"{city_data.get('population', 0):,} habitants"],
        ['Type de diagnostic:', diagnostic_info.get('type', 'N/A')],
        ['Date de création:', datetime.now().strftime('%d/%m/%Y')],
    ]
    
    info_table = Table(info_data, colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(info_table)
    story.append(PageBreak())
    
    # Résumé exécutif
    story.append(Paragraph("RÉSUMÉ EXÉCUTIF", heading_style))
    story.append(Paragraph(diagnostic_info.get('objective', ''), normal_style))
    
    # Calcul des scores par dimension
    dimension_scores = {}
    for category, indicators in indicators_data.items():
        values = [ind['value'] for ind in indicators.values() if not pd.isna(ind['value']) and ind['value'] != 0]
        if values:
            dimension_scores[category] = np.mean(values)
        else:
            dimension_scores[category] = 0
    
    # Synthèse des scores
    story.append(Spacer(1, 15))
    story.append(Paragraph("Synthèse des Scores par Dimension", ParagraphStyle(
        'ScoreHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#495057')
    )))
    
    score_data = [['Dimension', 'Score Moyen', 'Évaluation']]
    for category, score in dimension_scores.items():
        if score >= 70:
            evaluation = "Excellent"
            color = colors.green
        elif score >= 50:
            evaluation = "Satisfaisant"
            color = colors.orange
        else:
            evaluation = "À améliorer"
            color = colors.red
            
        score_data.append([category, f"{score:.1f}", evaluation])
    
    score_table = Table(score_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    
    story.append(score_table)
    story.append(PageBreak())
    
    # Analyse détaillée par dimension
    for category, indicators in indicators_data.items():
        story.append(Paragraph(f"ANALYSE - {category.upper()}", heading_style))
        
        # Description de la dimension
        descriptions = {
            "Société": "Cette dimension évalue les aspects sociodémographiques et de développement humain de la ville.",
            "Logement": "Cette dimension analyse l'accès aux services de base et la qualité de l'habitat.",
            "Développement Spatial": "Cette dimension examine l'organisation spatiale et l'aménagement du territoire urbain.",
            "Infrastructure": "Cette dimension évalue la qualité et l'accessibilité des infrastructures urbaines.",
            "Environnement": "Cette dimension analyse la durabilité environnementale et la résilience climatique.",
            "Gouvernance": "Cette dimension évalue l'efficacité des institutions et la participation citoyenne.",
            "Économie": "Cette dimension analyse la performance économique et les opportunités d'emploi."
        }
        
        story.append(Paragraph(descriptions.get(category, ""), normal_style))
        story.append(Spacer(1, 10))
        
        # Tableau des indicateurs pour cette dimension
        table_data = [['Indicateur', 'Valeur', 'Unité', 'Année', 'Source']]
        
        for code, data in indicators.items():
            value = data['value'] if not pd.isna(data['value']) else 'N/A'
            if isinstance(value, (int, float)) and not pd.isna(value):
                if abs(value) >= 1000:
                    value_str = f"{value:,.0f}"
                else:
                    value_str = f"{value:.2f}"
            else:
                value_str = str(value)
                
            table_data.append([
                data['name'],
                value_str,
                data['unit'],
                str(data['year']) if data['year'] else 'N/A',
                data['source'][:30] + '...' if len(data['source']) > 30 else data['source']
            ])
        
        table = Table(table_data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Recommandations stratégiques
    story.append(PageBreak())
    story.append(Paragraph("RECOMMANDATIONS STRATÉGIQUES", heading_style))
    
    recommendations = {
        "Court terme (0-2 ans)": [
            "Améliorer l'accès aux services de base (eau, électricité, assainissement)",
            "Renforcer la collecte et le traitement des déchets",
            "Développer les systèmes d'information urbaine"
        ],
        "Moyen terme (2-5 ans)": [
            "Développer les infrastructures de transport et de communication",
            "Mettre en place des mécanismes de participation citoyenne",
            "Promouvoir l'économie locale et l'emploi"
        ],
        "Long terme (5-10 ans)": [
            "Développer une planification urbaine intégrée",
            "Renforcer la résilience climatique",
            "Créer des pôles économiques durables"
        ]
    }
    
    for timeframe, recs in recommendations.items():
        story.append(Paragraph(timeframe, ParagraphStyle(
            'TimeframeHeading',
            parent=styles['Heading3'],
            fontSize=13,
            spaceAfter=8,
            textColor=colors.HexColor('#495057'),
            fontName='Helvetica-Bold'
        )))
        
        for i, rec in enumerate(recs, 1):
            story.append(Paragraph(f"{i}. {rec}", normal_style))
        
        story.append(Spacer(1, 10))
    
    # Conclusion
    story.append(Spacer(1, 20))
    story.append(Paragraph("CONCLUSION ET PERSPECTIVES", heading_style))
    
    conclusion_text = f"""
    Ce diagnostic urbain de {city_data.get('city', 'la ville')} révèle un profil urbain avec des forces et des défis spécifiques. 
    Les données collectées et analysées fournissent une base solide pour orienter les politiques urbaines et les investissements prioritaires.
    
    Il est recommandé de mettre à jour ce diagnostic tous les 2-3 ans pour suivre l'évolution des indicateurs et ajuster les stratégies 
    de développement urbain en conséquence.
    
    Ce rapport constitue un outil de pilotage pour les décideurs locaux et les partenaires au développement, permettant une approche 
    basée sur les données pour le développement urbain durable.
    """
    
    story.append(Paragraph(conclusion_text, normal_style))
    
    # Annexes
    if documents_info:
        story.append(PageBreak())
        story.append(Paragraph("ANNEXES - DOCUMENTS DE RÉFÉRENCE", heading_style))
        
        for i, doc in enumerate(documents_info, 1):
            story.append(Paragraph(f"Annexe {i}: {doc['filename']}", ParagraphStyle(
                'AnnexHeading',
                parent=styles['Heading4'],
                fontSize=12,
                spaceAfter=5,
                textColor=colors.HexColor('#6c757d')
            )))
            story.append(Paragraph(f"Type: {doc['type']}", normal_style))
            story.append(Paragraph(f"Taille: {doc['size']} caractères", normal_style))
            story.append(Spacer(1, 10))
    
    # Génération du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Fonction de génération de réponse IA avancée
def generate_advanced_ai_response(prompt, context_data=None, documents=None):
    """Génère une réponse IA avancée combinant données locales et web"""
    
    # Réponses contextuelles basées sur les données
    if context_data and 'indicators_data' in context_data:
        indicators_data = context_data['indicators_data']
        city_name = context_data.get('city_data', {}).get('city', 'la ville')
        
        # Analyse des mots-clés dans la question
        prompt_lower = prompt.lower()
        
        # Réponses spécifiques aux indicateurs
        if any(word in prompt_lower for word in ['population', 'démographie', 'habitants']):
            pop_data = None
            for category, indicators in indicators_data.items():
                for code, data in indicators.items():
                    if 'population' in data['name'].lower():
                        pop_data = data
                        break
            
            if pop_data and not pd.isna(pop_data['value']):
                return f"Selon les données collectées, {city_name} compte {pop_data['value']:,.0f} habitants (source: {pop_data['source']}, {pop_data['year']}). Cette information est cruciale pour la planification urbaine et l'allocation des ressources."
        
        elif any(word in prompt_lower for word in ['eau', 'assainissement', 'électricité']):
            services_info = []
            for category, indicators in indicators_data.items():
                if category == "Logement":
                    for code, data in indicators.items():
                        if any(service in data['name'].lower() for service in ['eau', 'assainissement', 'électricité']):
                            if not pd.isna(data['value']):
                                services_info.append(f"- {data['name']}: {data['value']:.1f}% (source: {data['source']})")
            
            if services_info:
                return f"Voici l'état des services de base à {city_name}:\n" + "\n".join(services_info) + "\n\nCes indicateurs sont essentiels pour évaluer la qualité de vie urbaine."
        
        elif any(word in prompt_lower for word in ['économie', 'pib', 'chômage', 'pauvreté']):
            econ_info = []
            for category, indicators in indicators_data.items():
                if category == "Économie":
                    for code, data in indicators.items():
                        if not pd.isna(data['value']):
                            econ_info.append(f"- {data['name']}: {data['value']:.2f} {data['unit']} (source: {data['source']})")
            
            if econ_info:
                return f"Situation économique de {city_name}:\n" + "\n".join(econ_info) + "\n\nCes données économiques orientent les stratégies de développement local."
    
    # Recherche dans les documents si disponibles
    if documents:
        rag_model = init_rag_system()
        if rag_model:
            search_results = search_in_documents(prompt, documents, rag_model)
            if search_results:
                relevant_content = search_results[0]['content'][:500]
                return f"D'après les documents analysés: {relevant_content}... \n\nCette information provient du document '{search_results[0]['metadata']['filename']}'."
    
    # Réponses générales sur le diagnostic urbain
    general_responses = {
        "diagnostic": "Un diagnostic urbain est une évaluation systématique de l'état d'une ville qui analyse ses dimensions sociales, économiques, environnementales et de gouvernance. Il sert de base pour identifier les priorités d'intervention et orienter les politiques urbaines.",
        
        "indicateurs": "Les indicateurs urbains sont des mesures quantitatives qui permettent d'évaluer les performances d'une ville dans différents domaines. Notre plateforme utilise 7 dimensions principales avec plus de 40 indicateurs couvrant tous les aspects du développement urbain.",
        
        "méthodologie": "Notre méthodologie combine la collecte automatique de données via des APIs internationales (Banque Mondiale, ONU-Habitat) avec la possibilité de saisie manuelle pour les indicateurs locaux. L'analyse utilise des techniques d'IA pour générer des insights et des recommandations.",
        
        "recommandations": "Les recommandations sont générées en analysant les scores des différentes dimensions et en identifiant les domaines prioritaires d'intervention. Elles sont structurées par horizon temporel (court, moyen, long terme) pour faciliter la planification.",
        
        "données": "La qualité des données est cruciale pour un diagnostic fiable. Nous privilégions les sources officielles et internationales, tout en permettant l'intégration de données locales. Chaque indicateur est documenté avec sa source et sa date de collecte."
    }
    
    # Recherche de correspondance dans les réponses générales
    for key, response in general_responses.items():
        if key in prompt_lower:
            return response
    
    # Réponse par défaut
    return """Je suis votre assistant IA pour le diagnostic urbain. Je peux vous aider avec:

🔍 **Analyse des indicateurs** - Interprétation des données collectées
📊 **Méthodologie** - Explication des méthodes d'évaluation  
📈 **Recommandations** - Suggestions d'amélioration basées sur les données
🏙️ **Planification urbaine** - Conseils pour le développement urbain
📚 **Recherche documentaire** - Analyse de vos documents uploadés

Posez-moi une question plus spécifique pour obtenir une réponse détaillée!"""

# Interface principale
def main():
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>🏙️ Diagnostic Urbain Intelligent</h1>
        <p>Plateforme d'analyse urbaine basée sur l'IA pour les villes africaines</p>
        <p><em>Collecte automatique • Analyse IA • Rapports professionnels</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de la base de données
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_database()
    
    # Navigation principale avec descriptions
    tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "📊 Dashboard", "🤖 Chatbot"])
    
    with tab1:
        st.markdown("""
        <div class="tab-description">
            <h3>🔍 Diagnostic Urbain Complet</h3>
            <p><strong>Créez un diagnostic professionnel de votre ville</strong> en suivant notre processus guidé :</p>
            <ul>
                <li>✅ Saisie des informations de base</li>
                <li>📄 Upload de documents techniques</li>
                <li>🔄 Collecte automatique des indicateurs</li>
                <li>✏️ Validation et ajustement des données</li>
                <li>📊 Génération du rapport PDF professionnel</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        diagnostic_tab()
    
    with tab2:
        st.markdown("""
        <div class="tab-description">
            <h3>📊 Dashboard Interactif</h3>
            <p><strong>Visualisez et analysez vos données</strong> à travers des graphiques interactifs :</p>
            <ul>
                <li>📈 Métriques clés par dimension</li>
                <li>🕸️ Graphique radar du profil urbain</li>
                <li>📊 Analyses comparatives</li>
                <li>📋 Tableaux détaillés des indicateurs</li>
            </ul>
            <p><em>Disponible après completion d'un diagnostic</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        dashboard_tab()
    
    with tab3:
        st.markdown("""
        <div class="tab-description">
            <h3>🤖 Assistant IA Spécialisé</h3>
            <p><strong>Obtenez des réponses expertes</strong> sur le diagnostic urbain :</p>
            <ul>
                <li>🧠 Analyse intelligente de vos données</li>
                <li>📚 Recherche dans vos documents (RAG)</li>
                <li>🌐 Accès aux meilleures pratiques internationales</li>
                <li>💡 Recommandations personnalisées</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        chatbot_tab()

def diagnostic_tab():
    """Onglet principal de diagnostic avec workflow complet"""
    
    # Étape 1: Informations de base
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.subheader("🌍 Informations de Base de la Ville")
    
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input(
            "Nom de la ville *", 
            placeholder="Ex: Nouakchott",
            help="Nom officiel de la ville à diagnostiquer"
        )
        country = st.selectbox(
            "Pays *",
            ["", "Mauritanie", "Sénégal", "Mali", "Burkina Faso", "Niger", "Tchad", 
             "Maroc", "Algérie", "Tunisie", "Côte d'Ivoire", "Ghana", "Nigeria", "Autre"],
            help="Sélectionnez le pays pour la collecte automatique des données"
        )
    
    with col2:
        region = st.text_input(
            "Région/Province", 
            placeholder="Ex: Nouakchott-Ouest",
            help="Division administrative de la ville"
        )
        population = st.number_input(
            "Population estimée", 
            min_value=0, 
            value=1000000,
            step=10000,
            help="Population actuelle estimée (sera mise à jour avec les données officielles)"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Étape 2: Documents techniques
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.subheader("📄 Documents Techniques et Données")
    
    st.markdown("""
    **Téléchargez vos documents de référence** pour enrichir l'analyse :
    - 📋 Plans d'urbanisme et schémas directeurs
    - 📊 Études sectorielles et rapports techniques  
    - 📈 Données statistiques locales (CSV, Excel)
    - 📑 Rapports d'évaluation existants
    """)
    
    uploaded_files = st.file_uploader(
        "Sélectionner les fichiers",
        type=['pdf', 'csv', 'xlsx', 'xls', 'docx'],
        accept_multiple_files=True,
        help="Formats supportés: PDF, CSV, Excel, Word. Taille max: 200MB par fichier"
    )
    
    # Traitement des documents uploadés
    processed_documents = []
    if uploaded_files:
        with st.spinner("Traitement des documents en cours..."):
            processed_documents = process_uploaded_documents(uploaded_files)
        
        if processed_documents:
            st.success(f"✅ {len(processed_documents)} document(s) traité(s) avec succès")
            
            # Aperçu des documents
            with st.expander("📋 Aperçu des documents traités"):
                for doc in processed_documents:
                    st.write(f"**{doc['filename']}** ({doc['type']}) - {doc['size']} caractères")
                    if doc['content']:
                        st.text(doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Étape 3: Type et objectif du diagnostic
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.subheader("🎯 Configuration du Diagnostic")
    
    col1, col2 = st.columns(2)
    
    with col1:
        diagnostic_type = st.selectbox(
            "Type de diagnostic *",
            ["", "Diagnostic général", "Diagnostic thématique - Logement", 
             "Diagnostic thématique - Transport", "Diagnostic thématique - Environnement", 
             "Diagnostic thématique - Économie", "Diagnostic thématique - Social",
             "Diagnostic thématique - Gouvernance"],
            help="Le type influence les indicateurs prioritaires et les recommandations"
        )
    
    with col2:
        target_audience = st.multiselect(
            "Public cible du rapport",
            ["Autorités locales", "Gouvernement national", "Bailleurs de fonds", 
             "ONG", "Secteur privé", "Citoyens", "Chercheurs", "Partenaires techniques"],
            default=["Autorités locales", "Bailleurs de fonds"],
            help="Influence le niveau de détail et le langage du rapport"
        )
    
    diagnostic_objective = st.text_area(
        "Objectif spécifique du diagnostic *",
        value="Évaluer l'état actuel du développement urbain et identifier les priorités d'intervention pour améliorer les conditions de vie des habitants et promouvoir un développement urbain durable.",
        height=120,
        help="Décrivez précisément les objectifs et l'utilisation prévue de ce diagnostic"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Étape 4: Collecte automatique des indicateurs
    if city and country and diagnostic_type:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("🔄 Collecte Automatique des Indicateurs")
        
        st.markdown(f"""
        **Prêt pour la collecte automatique** pour **{city}, {country}**
        
        🌐 **Sources de données :**
        - Banque Mondiale (World Bank Open Data)
        - Indicateurs de développement urbain
        - Données socio-économiques nationales
        - Statistiques environnementales
        
        ⏱️ **Durée estimée :** 2-3 minutes
        """)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("🚀 Lancer la Collecte", type="primary", use_container_width=True):
                with st.spinner("🔍 Collecte des données en cours..."):
                    # Mapping des pays vers codes ISO
                    country_codes = {
                        "Mauritanie": "MR", "Sénégal": "SN", "Mali": "ML", 
                        "Burkina Faso": "BF", "Niger": "NE", "Tchad": "TD",
                        "Maroc": "MA", "Algérie": "DZ", "Tunisie": "TN",
                        "Côte d'Ivoire": "CI", "Ghana": "GH", "Nigeria": "NG"
                    }
                    
                    country_code = country_codes.get(country, "MR")
                    collected_data = collect_worldbank_data(country_code, INDICATORS)
                    
                    # Sauvegarde dans la session
                    st.session_state.collected_data = collected_data
                    st.session_state.processed_documents = processed_documents
                    
                    # Statistiques de collecte
                    total_indicators = sum(len(indicators) for indicators in collected_data.values())
                    collected_indicators = sum(
                        1 for indicators in collected_data.values() 
                        for data in indicators.values() 
                        if not pd.isna(data['value'])
                    )
                    
                    st.success(f"✅ Collecte terminée ! {collected_indicators}/{total_indicators} indicateurs collectés")
        
        with col2:
            if 'collected_data' in st.session_state:
                # Affichage des statistiques de collecte
                total_indicators = sum(len(indicators) for indicators in st.session_state.collected_data.values())
                collected_indicators = sum(
                    1 for indicators in st.session_state.collected_data.values() 
                    for data in indicators.values() 
                    if not pd.isna(data['value'])
                )
                
                success_rate = (collected_indicators / total_indicators) * 100
                
                st.metric(
                    "Taux de collecte", 
                    f"{success_rate:.1f}%",
                    f"{collected_indicators}/{total_indicators} indicateurs"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Étape 5: Validation et ajustement des indicateurs
        if 'collected_data' in st.session_state:
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("✅ Validation et Ajustement des Indicateurs")
            
            st.markdown("""
            **Vérifiez et ajustez les données collectées** selon vos connaissances locales :
            - ✏️ Modifiez les valeurs si nécessaire
            - 💬 Ajoutez des commentaires explicatifs
            - 📎 Précisez les sources locales
            """)
            
            validated_data = {}
            
            # Onglets par dimension pour une meilleure organisation
            dimension_tabs = st.tabs(list(st.session_state.collected_data.keys()))
            
            for i, (category, indicators) in enumerate(st.session_state.collected_data.items()):
                with dimension_tabs[i]:
                    st.markdown(f"### 📊 Dimension: {category}")
                    
                    validated_data[category] = {}
                    
                    for code, data in indicators.items():
                        # Interface pour chaque indicateur
                        with st.container():
                            st.markdown('<div class="indicator-row">', unsafe_allow_html=True)
                            
                            col1, col2, col3, col4 = st.columns([3, 1.5, 1, 2.5])
                            
                            with col1:
                                st.markdown(f"**📈 {data['name']}**")
                                st.caption(f"Source: {data['source']}")
                            
                            with col2:
                                current_value = data['value'] if not pd.isna(data['value']) else 0.0
                                new_value = st.number_input(
                                    "Valeur", 
                                    value=float(current_value),
                                    key=f"val_{code}",
                                    format="%.3f",
                                    help=f"Valeur actuelle: {current_value}"
                                )
                            
                            with col3:
                                st.markdown(f"**{data['unit']}**")
                                if data['year']:
                                    st.caption(f"Année: {data['year']}")
                            
                            with col4:
                                comment = st.text_input(
                                    "Commentaire/Source locale",
                                    key=f"comment_{code}",
                                    placeholder="Optionnel - précisions locales",
                                    help="Ajoutez des informations contextuelles"
                                )
                            
                            # Sauvegarde des données validées
                            validated_data[category][code] = {
                                'name': data['name'],
                                'value': new_value,
                                'unit': data['unit'],
                                'year': data['year'],
                                'source': data['source'],
                                'comment': comment,
                                'wb_available': data.get('wb_available', False)
                            }
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown("---")
            
            # Sauvegarde des données validées
            st.session_state.validated_data = validated_data
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Étape 6: Génération du rapport
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("📄 Génération du Rapport Final")
            
            st.markdown("""
            **Votre diagnostic est prêt !** Le rapport PDF inclura :
            - 📋 Résumé exécutif avec scores par dimension
            - 📊 Analyse détaillée de chaque dimension  
            - 📈 Tableaux et graphiques professionnels
            - 💡 Recommandations stratégiques personnalisées
            - 📚 Annexes avec vos documents de référence
            """)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("📄 Générer le Rapport PDF", type="primary", use_container_width=True):
                    with st.spinner("🔄 Génération du rapport professionnel en cours..."):
                        # Préparation des données
                        city_data = {
                            'city': city,
                            'country': country,
                            'region': region,
                            'population': population
                        }
                        
                        diagnostic_info = {
                            'type': diagnostic_type,
                            'objective': diagnostic_objective,
                            'target_audience': target_audience
                        }
                        
                        # Génération du PDF avancé
                        pdf_buffer = generate_advanced_pdf_report(
                            city_data, 
                            validated_data, 
                            diagnostic_info,
                            processed_documents
                        )
                        
                        # Bouton de téléchargement
                        st.download_button(
                            label="📥 Télécharger le Rapport PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"diagnostic_urbain_{city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Sauvegarde pour le dashboard
                        st.session_state.final_report_data = {
                            'city_data': city_data,
                            'indicators_data': validated_data,
                            'diagnostic_info': diagnostic_info,
                            'documents': processed_documents
                        }
                        
                        st.success("✅ Rapport généré avec succès ! Vous pouvez maintenant accéder au Dashboard.")
                        st.balloons()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Message d'aide si les champs obligatoires ne sont pas remplis
        st.info("👆 Veuillez remplir les informations de base (ville, pays, type de diagnostic) pour continuer")

def dashboard_tab():
    """Dashboard interactif avec visualisations avancées"""
    
    if 'final_report_data' not in st.session_state:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; margin: 2rem 0;">
            <h3>📊 Dashboard en attente</h3>
            <p>Veuillez d'abord compléter un diagnostic dans l'onglet <strong>'🔍 Diagnostic'</strong></p>
            <p>Le dashboard se remplira automatiquement avec vos données analysées</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Récupération des données
    data = st.session_state.final_report_data
    city_data = data['city_data']
    indicators_data = data['indicators_data']
    diagnostic_info = data['diagnostic_info']
    
    # En-tête du dashboard
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;">
        <h2>📊 Dashboard - {city_data['city']}</h2>
        <p>{city_data['country']} • Population: {city_data['population']:,} habitants</p>
        <p><em>{diagnostic_info['type']}</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Calcul des scores par dimension
    dimension_scores = {}
    dimension_details = {}
    
    for category, indicators in indicators_data.items():
        values = []
        valid_indicators = 0
        total_indicators = len(indicators)
        
        for code, data in indicators.items():
            if not pd.isna(data['value']) and data['value'] != 0:
                values.append(abs(data['value']))  # Valeur absolue pour éviter les scores négatifs
                vali
valid_indicators += 1
        
        if values:
            # Normalisation des scores (0-100)
            avg_value = np.mean(values)
            # Score basé sur la moyenne normalisée (ajustement selon le contexte)
            if category in ["Société", "Logement", "Infrastructure"]:
                # Pour ces dimensions, plus c'est élevé, mieux c'est
                score = min(100, avg_value)
            elif category == "Environnement":
                # Pour l'environnement, certains indicateurs sont inversés (pollution)
                score = max(0, 100 - avg_value) if avg_value > 50 else avg_value
            else:
                score = min(100, avg_value)
            
            dimension_scores[category] = score
        else:
            dimension_scores[category] = 0
        
        dimension_details[category] = {
            'score': dimension_scores[category],
            'valid_indicators': valid_indicators,
            'total_indicators': total_indicators,
            'completion_rate': (valid_indicators / total_indicators) * 100
        }
    
    # Métriques principales
    st.subheader("🎯 Métriques Clés")
    
    cols = st.columns(len(dimension_scores))
    for i, (category, score) in enumerate(dimension_scores.items()):
        with cols[i]:
            # Couleur basée sur le score
            if score >= 70:
                color = "#28a745"
                status = "Excellent"
            elif score >= 50:
                color = "#ffc107"
                status = "Satisfaisant"
            else:
                color = "#dc3545"
                status = "À améliorer"
            
            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 0.9rem;">{category}</h4>
                <h2 style="margin: 0.5rem 0; font-size: 2rem;">{score:.1f}</h2>
                <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">{status}</p>
                <p style="margin: 0; font-size: 0.7rem; opacity: 0.8;">{dimension_details[category]['valid_indicators']}/{dimension_details[category]['total_indicators']} indicateurs</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕸️ Profil Urbain - Radar")
        
        # Graphique radar
        categories = list(dimension_scores.keys())
        values = list(dimension_scores.values())
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=city_data['city'],
            line=dict(color='#2a5298', width=3),
            fillcolor='rgba(42, 82, 152, 0.3)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10),
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#495057')
                )
            ),
            showlegend=False,
            title=dict(
                text=f"Profil de {city_data['city']}",
                x=0.5,
                font=dict(size=16, color='#2a5298')
            ),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        st.subheader("📊 Scores par Dimension")
        
        # Graphique en barres
        fig_bar = px.bar(
            x=list(dimension_scores.values()),
            y=list(dimension_scores.keys()),
            orientation='h',
            color=list(dimension_scores.values()),
            color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
            range_color=[0, 100]
        )
        
        fig_bar.update_layout(
            title=dict(
                text="Performance par Dimension",
                font=dict(size=16, color='#2a5298')
            ),
            xaxis_title="Score (0-100)",
            yaxis_title="",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        fig_bar.update_traces(
            texttemplate='%{x:.1f}',
            textposition='inside',
            textfont=dict(color='white', size=12)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Analyse détaillée par dimension
    st.subheader("🔍 Analyse Détaillée par Dimension")
    
    # Sélecteur de dimension
    selected_dimension = st.selectbox(
        "Choisir une dimension à analyser",
        list(indicators_data.keys()),
        help="Sélectionnez une dimension pour voir le détail des indicateurs"
    )
    
    if selected_dimension:
        dimension_data = indicators_data[selected_dimension]
        
        # Statistiques de la dimension
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Score Global",
                f"{dimension_scores[selected_dimension]:.1f}/100",
                help="Score moyen de la dimension"
            )
        
        with col2:
            completion = dimension_details[selected_dimension]['completion_rate']
            st.metric(
                "Complétude",
                f"{completion:.1f}%",
                help="Pourcentage d'indicateurs avec des données"
            )
        
        with col3:
            valid_count = dimension_details[selected_dimension]['valid_indicators']
            st.metric(
                "Indicateurs Valides",
                f"{valid_count}",
                help="Nombre d'indicateurs avec des données"
            )
        
        with col4:
            total_count = dimension_details[selected_dimension]['total_indicators']
            st.metric(
                "Total Indicateurs",
                f"{total_count}",
                help="Nombre total d'indicateurs dans cette dimension"
            )
        
        # Tableau détaillé des indicateurs
        st.markdown("### 📋 Détail des Indicateurs")
        
        # Préparation des données pour le tableau
        table_data = []
        for code, data in dimension_data.items():
            value = data['value'] if not pd.isna(data['value']) else 'N/A'
            if isinstance(value, (int, float)) and not pd.isna(value):
                if abs(value) >= 1000:
                    value_str = f"{value:,.1f}"
                else:
                    value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            
            # Statut basé sur la disponibilité des données
            status = "✅ Disponible" if not pd.isna(data['value']) else "❌ Manquant"
            
            table_data.append({
                'Indicateur': data['name'],
                'Valeur': value_str,
                'Unité': data['unit'],
                'Année': data['year'] if data['year'] else 'N/A',
                'Source': data['source'][:40] + '...' if len(data['source']) > 40 else data['source'],
                'Statut': status,
                'Commentaire': data.get('comment', '') or 'Aucun'
            })
        
        # Affichage du tableau avec filtres
        df_table = pd.DataFrame(table_data)
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filtrer par statut",
                ["✅ Disponible", "❌ Manquant"],
                default=["✅ Disponible", "❌ Manquant"]
            )
        
        with col2:
            search_term = st.text_input(
                "Rechercher un indicateur",
                placeholder="Tapez pour filtrer..."
            )
        
        # Application des filtres
        filtered_df = df_table[df_table['Statut'].isin(status_filter)]
        if search_term:
            filtered_df = filtered_df[
                filtered_df['Indicateur'].str.contains(search_term, case=False, na=False)
            ]
        
        # Affichage du tableau filtré
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Indicateur': st.column_config.TextColumn('Indicateur', width='large'),
                'Valeur': st.column_config.TextColumn('Valeur', width='small'),
                'Unité': st.column_config.TextColumn('Unité', width='small'),
                'Année': st.column_config.TextColumn('Année', width='small'),
                'Source': st.column_config.TextColumn('Source', width='medium'),
                'Statut': st.column_config.TextColumn('Statut', width='small'),
                'Commentaire': st.column_config.TextColumn('Commentaire', width='medium')
            }
        )
    
    # Graphiques comparatifs
    st.subheader("📈 Analyses Comparatives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de complétude des données
        completion_data = {
            'Dimension': list(dimension_details.keys()),
            'Taux de Complétude (%)': [details['completion_rate'] for details in dimension_details.values()]
        }
        
        fig_completion = px.bar(
            completion_data,
            x='Taux de Complétude (%)',
            y='Dimension',
            orientation='h',
            title="Complétude des Données par Dimension",
            color='Taux de Complétude (%)',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig_completion.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        fig_completion.update_traces(
            texttemplate='%{x:.1f}%',
            textposition='inside'
        )
        
        st.plotly_chart(fig_completion, use_container_width=True)
    
    with col2:
        # Graphique de distribution des scores
        fig_dist = px.pie(
            values=list(dimension_scores.values()),
            names=list(dimension_scores.keys()),
            title="Distribution des Scores par Dimension",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig_dist.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=10
        )
        
        fig_dist.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # Recommandations basées sur les données
    st.subheader("💡 Recommandations Intelligentes")
    
    # Analyse automatique des points faibles
    weak_dimensions = [dim for dim, score in dimension_scores.items() if score < 50]
    strong_dimensions = [dim for dim, score in dimension_scores.items() if score >= 70]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if weak_dimensions:
            st.markdown("#### 🔴 Dimensions Prioritaires")
            for dim in weak_dimensions:
                score = dimension_scores[dim]
                st.markdown(f"""
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin-bottom: 0.5rem; border-radius: 5px;">
                    <strong>{dim}</strong> (Score: {score:.1f}/100)<br>
                    <small>Nécessite une attention immédiate et des investissements prioritaires</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Aucune dimension critique identifiée")
    
    with col2:
        if strong_dimensions:
            st.markdown("#### 🟢 Points Forts")
            for dim in strong_dimensions:
                score = dimension_scores[dim]
                st.markdown(f"""
                <div style="background: #d1edff; border-left: 4px solid #28a745; padding: 1rem; margin-bottom: 0.5rem; border-radius: 5px;">
                    <strong>{dim}</strong> (Score: {score:.1f}/100)<br>
                    <small>Performance satisfaisante, maintenir les efforts</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Aucun point fort majeur identifié")
    
    # Export des données
    st.subheader("📤 Export des Données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export CSV des indicateurs
        all_indicators_data = []
        for category, indicators in indicators_data.items():
            for code, data in indicators.items():
                all_indicators_data.append({
                    'Dimension': category,
                    'Code': code,
                    'Indicateur': data['name'],
                    'Valeur': data['value'],
                    'Unité': data['unit'],
                    'Année': data['year'],
                    'Source': data['source'],
                    'Commentaire': data.get('comment', '')
                })
        
        df_export = pd.DataFrame(all_indicators_data)
        csv_data = df_export.to_csv(index=False)
        
        st.download_button(
            label="📊 Export CSV",
            data=csv_data,
            file_name=f"indicateurs_{city_data['city']}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export JSON des scores
        scores_data = {
            'ville': city_data,
            'scores_dimensions': dimension_scores,
            'details_dimensions': dimension_details,
            'date_export': datetime.now().isoformat()
        }
        
        json_data = json.dumps(scores_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📋 Export JSON",
            data=json_data,
            file_name=f"scores_{city_data['city']}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Régénération du rapport PDF
        if st.button("🔄 Régénérer PDF", use_container_width=True):
            with st.spinner("Génération en cours..."):
                pdf_buffer = generate_advanced_pdf_report(
                    city_data, 
                    indicators_data, 
                    diagnostic_info,
                    data.get('documents', [])
                )
                
                st.download_button(
                    label="📥 Télécharger PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"diagnostic_urbain_{city_data['city']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

def chatbot_tab():
    """Interface de chatbot IA avancé"""
    
    st.markdown("### 🤖 Assistant IA Spécialisé en Diagnostic Urbain")
    
    # Initialisation de l'historique des conversations
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Informations sur les capacités du chatbot
    with st.expander("ℹ️ Capacités de l'Assistant IA"):
        st.markdown("""
        **🧠 Intelligence Hybride :**
        - **Analyse locale** : Traitement de vos données de diagnostic
        - **Recherche documentaire** : RAG sur vos documents uploadés
        - **Connaissances globales** : Meilleures pratiques internationales
        - **Recommandations** : Suggestions personnalisées basées sur vos données
        
        **💬 Types de questions supportées :**
        - Interprétation des indicateurs et scores
        - Comparaisons avec d'autres villes
        - Recommandations d'amélioration
        - Méthodologies de diagnostic urbain
        - Recherche dans vos documents
        """)
    
    # Zone de chat
    chat_container = st.container()
    
    # Affichage de l'historique des conversations
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 Vous :</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant :</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Interface de saisie
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Posez votre question :",
            placeholder="Ex: Comment interpréter le score de la dimension Logement ?",
            key="chat_input"
        )
    
    with col2:
        send_button = st.button("📤 Envoyer", type="primary", use_container_width=True)
    
    # Suggestions de questions
    st.markdown("**💡 Questions suggérées :**")
    
    suggestion_cols = st.columns(3)
    
    suggestions = [
        "Quels sont les points faibles de ma ville ?",
        "Comment améliorer le score de logement ?",
        "Comparez avec les standards internationaux",
        "Que disent mes documents sur l'urbanisme ?",
        "Quelles sont les priorités d'investissement ?",
        "Comment interpréter les indicateurs économiques ?"
    ]
    
    for i, suggestion in enumerate(suggestions):
        col_index = i % 3
        with suggestion_cols[col_index]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                user_input = suggestion
                send_button = True
    
    # Traitement de la question
    if (send_button and user_input) or user_input:
        if user_input.strip():
            # Ajout de la question à l'historique
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Préparation du contexte
            context_data = {}
            documents = []
            
            # Récupération des données du diagnostic si disponibles
            if 'final_report_data' in st.session_state:
                context_data = st.session_state.final_report_data
                documents = context_data.get('documents', [])
            elif 'processed_documents' in st.session_state:
                documents = st.session_state.processed_documents
            
            # Génération de la réponse
            with st.spinner("🤔 Réflexion en cours..."):
                response = generate_advanced_ai_response(
                    user_input, 
                    context_data, 
                    documents
                )
            
            # Ajout de la réponse à l'historique
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            
            # Rerun pour afficher la nouvelle conversation
            st.rerun()
    
    # Options avancées
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Effacer l'historique", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.session_state.chat_history:
            # Export de la conversation
            chat_export = "\n\n".join([
                f"{'👤 UTILISATEUR' if msg['role'] == 'user' else '🤖 ASSISTANT'}: {msg['content']}"
                for msg in st.session_state.chat_history
            ])
            
            st.download_button(
                label="📥 Export Chat",
                data=chat_export,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col3:
        # Statistiques de la conversation
        if st.session_state.chat_history:
            total_messages = len(st.session_state.chat_history)
            user_messages = len([msg for msg in st.session_state.chat_history if msg['role'] == 'user'])
            
            st.metric(
                "Messages échangés",
                f"{total_messages}",
                f"{user_messages} questions"
            )

# Point d'entrée principal
if __name__ == "__main__":
    main()
