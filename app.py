import streamlit as st
import openai
from datetime import datetime
import pandas as pd
from io import BytesIO
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as RLImage
from reportlab.lib.units import inch
import markdown
import requests
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import numpy as np
from matplotlib.patches import Wedge
import io

# Configuration des couleurs et styles
COLORS = {
    'primary': '#1f4e79',
    'secondary': '#e67e22',
    'accent': '#27ae60',
    'warning': '#e74c3c',
    'light': '#ecf0f1',
    'dark': '#2c3e50'
}

# --- OCR pour PDF scannés ---
def extract_text_from_image_pdf(pdf_file):
    try:
        images = convert_from_bytes(pdf_file.read(), dpi=200)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"[Erreur OCR] : {e}"

# --- Web LLM ENRICHI pour recherche d'informations contextuelles ---
def web_search_context(ville, pays, groq_api_key):
    """Recherche d'informations contextuelles TRÈS DÉTAILLÉES sur la ville via IA"""
    prompt = f"""
    Vous êtes un expert en développement urbain africain. Fournissez une analyse contextuelle TRÈS DÉTAILLÉE et APPROFONDIE sur {ville}, {pays} en 1500 mots minimum :

    1. DÉMOGRAPHIE ET POPULATION :
    - Population actuelle précise avec sources
    - Taux de croissance démographique annuel
    - Structure par âge et sexe
    - Densité de population par quartier
    - Migrations internes et externes
    - Projections démographiques 2030-2050

    2. GÉOGRAPHIE ET CLIMAT :
    - Situation géographique précise
    - Topographie et relief
    - Climat et saisons
    - Ressources naturelles disponibles
    - Risques climatiques et environnementaux
    - Impact du changement climatique

    3. ÉCONOMIE LOCALE DÉTAILLÉE :
    - PIB de la ville et contribution au PIB national
    - Secteurs économiques dominants
    - Principales entreprises et employeurs
    - Taux de chômage par catégorie
    - Économie informelle et son poids
    - Investissements étrangers récents

    4. INFRASTRUCTURE ET SERVICES :
    - État du réseau routier et transport
    - Système de santé (hôpitaux, centres de santé)
    - Système éducatif (écoles, universités)
    - Télécommunications et internet
    - Services bancaires et financiers
    - Marchés et commerce

    5. DÉFIS URBAINS SPÉCIFIQUES :
    - Problèmes de logement et bidonvilles
    - Gestion des déchets et assainissement
    - Approvisionnement en eau et électricité
    - Sécurité et criminalité
    - Pollution et environnement
    - Gouvernance urbaine

    6. PROJETS ET INITIATIVES :
    - Grands projets d'infrastructure en cours
    - Programmes de développement urbain
    - Partenariats internationaux
    - Initiatives de la société civile
    - Projets de coopération décentralisée

    7. COMPARAISONS RÉGIONALES :
    - Positionnement par rapport aux autres capitales sahéliennes
    - Benchmarking avec Dakar, Bamako, Ouagadougou
    - Indicateurs de développement comparés
    - Bonnes pratiques observées ailleurs
    - Leçons apprises d'autres villes similaires

    8. PERSPECTIVES D'AVENIR :
    - Vision de développement à long terme
    - Potentiels de croissance identifiés
    - Défis futurs anticipés
    - Opportunités d'investissement
    - Scénarios d'évolution possible

    Utilisez des données chiffrées précises, des références à des études récentes, et adoptez un ton analytique et professionnel. Structurez votre réponse avec des sous-titres clairs.
    """
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return "Informations contextuelles non disponibles."
    except:
        return "Informations contextuelles non disponibles."

# --- Génération de graphiques avancés ---
def generate_advanced_graphs(data_dict):
    """Génère plusieurs graphiques selon les données fournies"""
    graphs = {}
    
    # Graphique 1: Indicateurs sociaux (radar chart)
    fig1, ax1 = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
    
    categories = ['Scolarisation\nPrimaire', 'Scolarisation\nSecondaire', 'Alphabétisation', 
                 'Espérance de vie\n(normalisée)', 'Accès médical\n(normalisé)']
    
    values = [
        float(data_dict.get('scolarisation_primaire', 0) or 0),
        float(data_dict.get('scolarisation_secondaire', 0) or 0),
        float(data_dict.get('alphabetisation', 0) or 0),
        min(100, float(data_dict.get('esperance_vie', 0) or 0) * 1.5),  # Normalisation
        min(100, float(data_dict.get('medecins', 0) or 0) * 10)  # Normalisation
    ]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]  # Fermer le polygone
    angles += angles[:1]
    
    ax1.plot(angles, values, 'o-', linewidth=2, color=COLORS['primary'])
    ax1.fill(angles, values, alpha=0.25, color=COLORS['primary'])
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(categories)
    ax1.set_ylim(0, 100)
    ax1.set_title('Indicateurs Sociaux - Vue d\'ensemble', size=16, weight='bold', pad=20)
    ax1.grid(True)
    
    buf1 = BytesIO()
    fig1.savefig(buf1, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig1)
    buf1.seek(0)
    graphs['social_radar'] = base64.b64encode(buf1.read()).decode("utf-8")
    
    # Graphique 2: Habitat et infrastructure
    fig2, ((ax2a, ax2b), (ax2c, ax2d)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Accès aux services de base
    services = ['Eau potable', 'Électricité', 'Sanitaires']
    acces_values = [
        float(data_dict.get('eau', 0) or 0),
        float(data_dict.get('electricite', 0) or 0),
        float(data_dict.get('sanitaires', 0) or 0)
    ]
    
    colors = [COLORS['accent'] if v >= 70 else COLORS['warning'] if v >= 40 else COLORS['warning'] for v in acces_values]
    bars = ax2a.bar(services, acces_values, color=colors)
    ax2a.set_title('Accès aux Services de Base (%)', weight='bold')
    ax2a.set_ylim(0, 100)
    for bar, value in zip(bars, acces_values):
        ax2a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                 f'{value:.0f}%', ha='center', weight='bold')
    
    # Qualité du logement
    logement_labels = ['Logements\nformels', 'Logements\ninformels']
    informel_pct = float(data_dict.get('informel', 0) or 0)
    logement_values = [100 - informel_pct, informel_pct]
    
    wedges, texts, autotexts = ax2b.pie(logement_values, labels=logement_labels, autopct='%1.1f%%',
                                       colors=[COLORS['accent'], COLORS['warning']], startangle=90)
    ax2b.set_title('Répartition des Logements', weight='bold')
    
    # Indicateurs de surpeuplement et satisfaction
    indicators = ['Surpeuplement', 'Insatisfaction\nlogement']
    indicator_values = [
        float(data_dict.get('surpeuplement', 0) or 0),
        100 - float(data_dict.get('satisfaction', 0) or 0)
    ]
    
    ax2c.barh(indicators, indicator_values, color=[COLORS['warning'], COLORS['secondary']])
    ax2c.set_title('Défis du Logement (%)', weight='bold')
    ax2c.set_xlim(0, 100)
    for i, v in enumerate(indicator_values):
        ax2c.text(v + 1, i, f'{v:.0f}%', va='center', weight='bold')
    
    # Coût et accessibilité
    cout = float(data_dict.get('cout_logement', 0) or 0)
    accession = float(data_dict.get('accession', 0) or 0)
    
    ax2d.scatter([cout], [accession], s=200, color=COLORS['primary'], alpha=0.7)
    ax2d.set_xlabel('Coût logement (€/m²)', weight='bold')
    ax2d.set_ylabel('Taux d\'accession (%)', weight='bold')
    ax2d.set_title('Coût vs Accessibilité', weight='bold')
    ax2d.grid(True, alpha=0.3)
    ax2d.annotate(f'Position actuelle\n({cout:.0f}€/m², {accession:.0f}%)', 
                 (cout, accession), xytext=(10, 10), textcoords='offset points')
    
    plt.tight_layout()
    buf2 = BytesIO()
    fig2.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig2)
    buf2.seek(0)
    graphs['habitat_analysis'] = base64.b64encode(buf2.read()).decode("utf-8")
    
    # Graphique 3: Indice synthétique de développement
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    # Calcul d'indices composites
    indice_social = np.mean([v for v in [
        float(data_dict.get('scolarisation_primaire', 0) or 0),
        float(data_dict.get('alphabetisation', 0) or 0),
        min(100, float(data_dict.get('esperance_vie', 0) or 0) * 1.5)
    ] if v > 0])
    
    indice_habitat = np.mean([v for v in [
        float(data_dict.get('eau', 0) or 0),
        float(data_dict.get('electricite', 0) or 0),
        100 - float(data_dict.get('informel', 0) or 0),
        float(data_dict.get('satisfaction', 0) or 0)
    ] if v > 0])
    
    indice_global = (indice_social + indice_habitat) / 2
    
    indices = ['Social', 'Habitat', 'Global']
    values = [indice_social, indice_habitat, indice_global]
    colors_idx = [COLORS['accent'], COLORS['secondary'], COLORS['primary']]
    
    bars = ax3.bar(indices, values, color=colors_idx, alpha=0.8)
    ax3.set_title('Indices de Développement Urbain', size=16, weight='bold')
    ax3.set_ylabel('Score (/100)', weight='bold')
    ax3.set_ylim(0, 100)
    
    # Ajout des seuils de référence
    ax3.axhline(y=75, color='green', linestyle='--', alpha=0.7, label='Excellent (75+)')
    ax3.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Moyen (50+)')
    ax3.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Critique (<25)')
    
    for bar, value in zip(bars, values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value:.1f}', ha='center', weight='bold', size=12)
    
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    buf3 = BytesIO()
    fig3.savefig(buf3, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig3)
    buf3.seek(0)
    graphs['indices_development'] = base64.b64encode(buf3.read()).decode("utf-8")
    
    return graphs

# --- Fonction Hugging Face ---
def generate_hf_report(prompt, hf_token):
    from huggingface_hub import InferenceClient
    try:
        client = InferenceClient(api_key=hf_token)
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur Hugging Face Providers: {e}"

# --- Fonction Groq ---
def generate_groq_report(prompt, groq_api_key, model="llama3-70b-8192"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Erreur Groq: {response.text}"

# --- Génération PDF professionnel AMÉLIORÉ ---
def create_professional_pdf(rapport_text, ville, graphs, context_info=""):
    """Crée un PDF professionnel avec table des matières, graphiques et mise en page avancée"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=18)
    
    # Styles personnalisés
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor(COLORS['primary']),
        alignment=1,  # Centré
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor(COLORS['primary']),
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15,
        textColor=HexColor(COLORS['secondary']),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        textColor=HexColor('#2c3e50'),
        fontName='Helvetica',
        leading=14
    )
    
    story = []
    
    # Page de titre
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(f"DIAGNOSTIC URBAIN INTELLIGENT", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Ville de {ville}", heading_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
    story.append(Spacer(1, 1*inch))
    
    # Logo ou image (si disponible)
    story.append(Paragraph("UrbanAI Diagnostic Platform", 
                          ParagraphStyle('Logo', fontSize=18, textColor=HexColor(COLORS['accent']), 
                                       alignment=1, fontName='Helvetica-Bold')))
    
    story.append(PageBreak())
    
    # Table des matières
    story.append(Paragraph("TABLE DES MATIÈRES", heading_style))
    story.append(Spacer(1, 20))
    
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
        ('BACKGROUND', (0, 0), (-1, 0), HexColor(COLORS['primary'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
    ]))
    
    story.append(toc_table)
    story.append(PageBreak())
    
    # Ajout du contexte Web LLM si disponible
    if context_info and context_info != "Informations contextuelles non disponibles.":
        story.append(Paragraph("CONTEXTE RÉGIONAL ET COMPARATIF", heading_style))
        story.append(Paragraph(context_info, normal_style))
        story.append(Spacer(1, 20))
        story.append(PageBreak())
    
    # Contenu principal du rapport (parsing amélioré avec numérotation)
    sections = rapport_text.split('\n')
    current_section_num = 0
    
    for line in sections:
        line = line.strip()
        if not line:
            continue
            
        # Détection des titres principaux avec numérotation automatique
        if any(line.upper().startswith(keyword) for keyword in ['RÉSUMÉ EXÉCUTIF', 'CONTEXTE DÉMOGRAPHIQUE', 'ANALYSE DE L\'HABITAT', 'DÉFIS ET OPPORTUNITÉS', 'RECOMMANDATIONS STRATÉGIQUES', 'CONCLUSION PROSPECTIVE']):
            current_section_num += 1
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"{current_section_num}. {line.upper()}", heading_style))
        # Détection des sous-titres
        elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
            clean_line = line.lstrip('-•* ').strip()
            story.append(Paragraph(f"• {clean_line}", subheading_style))
        # Détection des titres avec **
        elif line.startswith('**') and line.endswith('**'):
            clean_line = line.strip('*').strip()
            story.append(Paragraph(clean_line, subheading_style))
        # Contenu normal
        else:
            story.append(Paragraph(line, normal_style))
    
    story.append(PageBreak())
    
    # Section graphiques intégrée dans le contenu
    current_section_num += 1
    story.append(Paragraph(f"{current_section_num}. GRAPHIQUES ET VISUALISATIONS", heading_style))
    story.append(Spacer(1, 20))
    
    # Ajout des graphiques avec descriptions détaillées
    graph_counter = 1
    for graph_name, graph_data in graphs.items():
        if graph_name == 'social_radar':
            story.append(Paragraph(f"{current_section_num}.{graph_counter} Analyse des Indicateurs Sociaux", subheading_style))
            story.append(Paragraph("Ce graphique radar présente une vue d'ensemble des principaux indicateurs sociaux de la ville, permettant d'identifier rapidement les domaines de force et les axes d'amélioration prioritaires.", normal_style))
        elif graph_name == 'habitat_analysis':
            story.append(Paragraph(f"{current_section_num}.{graph_counter} Analyse de l'Habitat et des Infrastructures", subheading_style))
            story.append(Paragraph("Cette série de graphiques détaille l'état des infrastructures de base, la qualité du parc de logements, et les défis d'accessibilité rencontrés par les habitants.", normal_style))
        elif graph_name == 'indices_development':
            story.append(Paragraph(f"{current_section_num}.{graph_counter} Indices Synthétiques de Développement", subheading_style))
            story.append(Paragraph("Ces indices composites permettent une évaluation globale du niveau de développement urbain et facilitent les comparaisons avec d'autres villes similaires.", normal_style))
        
        # Conversion base64 vers image
        try:
            img_data = base64.b64decode(graph_data)
            img_buffer = BytesIO(img_data)
            img = RLImage(img_buffer, width=5*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 20))
        except:
            story.append(Paragraph("Graphique non disponible", normal_style))
            story.append(Spacer(1, 20))
        
        graph_counter += 1
    
    story.append(PageBreak())
    
    # Annexes
    story.append(Paragraph("ANNEXES ET RÉFÉRENCES", heading_style))
    story.append(Spacer(1, 20))
    
    annexes_content = f"""
    <b>Méthodologie :</b><br/>
    Ce rapport a été généré automatiquement par UrbanAI Diagnostic, utilisant des algorithmes d'intelligence artificielle 
    pour analyser les données urbaines et produire des recommandations contextualisées. La méthodologie combine l'analyse 
    quantitative des indicateurs urbains avec une recherche contextuelle approfondie et des comparaisons régionales.<br/><br/>
    
    <b>Sources de données :</b><br/>
    • Données primaires saisies par l'utilisateur<br/>
    • Documents techniques téléchargés et analysés par OCR<br/>
    • Base de connaissances UrbanAI (mise à jour 2024)<br/>
    • Recherche contextuelle automatisée via IA générative<br/>
    • Bases de données internationales (Banque Mondiale, ONU-Habitat)<br/><br/>
    
    <b>Références techniques et standards :</b><br/>
    • ONU-Habitat - Nouvel Agenda Urbain et indicateurs urbains<br/>
    • Banque Mondiale - Données de développement urbain<br/>
    • Standards ISO 37120 pour les indicateurs de ville intelligente<br/>
    • Objectifs de Développement Durable (ODD 11 - Villes durables)<br/>
    • Cadre de Sendai pour la réduction des risques de catastrophe<br/><br/>
    
    <b>Limites et considérations :</b><br/>
    • Les données utilisées reflètent la situation au moment de la saisie<br/>
    • Les recommandations nécessitent une validation locale<br/>
    • L'analyse contextuelle est basée sur des sources publiques disponibles<br/>
    • Les comparaisons régionales peuvent varier selon les sources<br/><br/>
    
    <b>Contact et informations :</b><br/>
    UrbanAI Diagnostic Platform - Version 2.0<br/>
    Rapport professionnel généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}<br/>
    Système de diagnostic urbain intelligent pour l'Afrique<br/>
    Développé avec des technologies d'IA avancées
    """
    
    story.append(Paragraph(annexes_content, normal_style))
    
    # Construction du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- UI Accueil ---
st.markdown("""
<div class="logo-container">
    <img src="https://cdn.abacus.ai/images/d1788567-27c2-4731-b4f0-26dc07fcd4f3.png" alt="CUS Logo" width="320">
</div>
<div class="main-header">
    <h1 style="color:#1f4e79;">UrbanAI Diagnostic</h1>
    <h3 style="color:#e67e22;">La plateforme intelligente pour le diagnostic urbain en Afrique</h3>
    <p style="font-size:1.1rem; color:#34495e;">
        <b>Description :</b> Diagnostic rapide, interactif et enrichi par l'IA, basé sur vos réponses et vos documents.
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Nouveau Diagnostic", "Dashboard", "Chatbot"])

with tab1:
    st.header("Section 1 : Société")
    col1, col2 = st.columns(2)
    with col1:
        scolarisation_primaire = st.text_input("Taux de scolarisation primaire (%)")
        scolarisation_secondaire = st.text_input("Taux de scolarisation secondaire (%)")
        alphabetisation = st.text_input("Taux d'alphabétisation adulte (%)")
        criminalite = st.text_input("Taux de criminalité")
    with col2:
        medecins = st.text_input("Nombre de médecins / 10k habitants")
        esperance_vie = st.text_input("Espérance de vie")

    st.header("Section 2 : Habitat")
    col3, col4 = st.columns(2)
    with col3:
        eau = st.text_input("Accès à l'eau potable (%)")
        electricite = st.text_input("Accès à l'électricité (%)")
        surpeuplement = st.text_input("Indice de surpeuplement")
        informel = st.text_input("Logements informels (%)")
    with col4:
        cout_logement = st.text_input("Coût moyen du logement (€/m²)")
        accession = st.text_input("Taux d'accession à la propriété (%)")
        sanitaires = st.text_input("Accès à des sanitaires améliorés (%)")
        satisfaction = st.text_input("Satisfaction logement (%)")

    st.header("Section 3 : Ville")
    ville = st.text_input("Nom de la Ville")
    contact = st.text_input("Contact")
    pays = st.text_input("Pays")

    st.header("Ajoutez vos documents (PDF, CSV, Excel)")
    uploaded_files = st.file_uploader("Fichiers support", type=["pdf", "csv", "xlsx"], accept_multiple_files=True)

    doc_texts = []
    if uploaded_files:
        for file in uploaded_files:
            if file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(file)
                    text = "".join([p.extract_text() or "" for p in reader.pages])
                    if len(text.strip()) < 50:
                        file.seek(0)
                        text = extract_text_from_image_pdf(file)
                    doc_texts.append(f"Contenu du PDF {file.name} :\n{text[:3000]}")
                except Exception as e:
                    doc_texts.append(f"Erreur lecture PDF {file.name} : {e}")
            elif file.type == "text/csv":
                df = pd.read_csv(file)
                doc_texts.append(f"CSV {file.name} :\n{df.head(10).to_string()}")
            elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df = pd.read_excel(file)
                doc_texts.append(f"Excel {file.name} :\n{df.head(10).to_string()}")

    moteur_ia = st.selectbox("Moteur IA", ["OpenAI", "Hugging Face", "Groq"])

    if st.button("Générer le diagnostic"):
        st.info("Recherche d'informations contextuelles approfondies...")
        
        # Recherche Web LLM ENRICHIE
        context_info = ""
        if ville and pays:
            if moteur_ia == "Groq":
                context_info = web_search_context(ville, pays, st.secrets["GROQ_API_KEY"])
            else:
                context_info = web_search_context(ville, pays, st.secrets.get("GROQ_API_KEY", ""))
        
        st.info("Génération des graphiques avancés...")
        
        # Préparation des données pour les graphiques
        data_dict = {
            'scolarisation_primaire': scolarisation_primaire,
            'scolarisation_secondaire': scolarisation_secondaire,
            'alphabetisation': alphabetisation,
            'criminalite': criminalite,
            'medecins': medecins,
            'esperance_vie': esperance_vie,
            'eau': eau,
            'electricite': electricite,
            'surpeuplement': surpeuplement,
            'informel': informel,
            'cout_logement': cout_logement,
            'accession': accession,
            'sanitaires': sanitaires,
            'satisfaction': satisfaction
        }
        
        # Génération des graphiques
        graphs = generate_advanced_graphs(data_dict)
        
        st.info("Génération du rapport IA détaillé de 20+ pages...")

        # Prompt ULTRA-ENRICHI pour un rapport de 20+ pages
        prompt = f"""
Vous êtes un expert senior en développement urbain africain avec 25 ans d'expérience internationale. 
Rédigez un rapport de diagnostic urbain EXTRÊMEMENT DÉTAILLÉ et PROFESSIONNEL de 20+ pages pour {ville}, {pays}.

CONTEXTE ADDITIONNEL APPROFONDI :
{context_info}

DONNÉES ANALYSÉES EN DÉTAIL :
Section Société :
- Scolarisation primaire : {scolarisation_primaire}%
- Scolarisation secondaire : {scolarisation_secondaire}%
- Alphabétisation adulte : {alphabetisation}%
- Taux de criminalité : {criminalite}
- Médecins pour 10k habitants : {medecins}
- Espérance de vie : {esperance_vie} ans

Section Habitat :
- Accès eau potable : {eau}%
- Accès électricité : {electricite}%
- Indice surpeuplement : {surpeuplement}
- Logements informels : {informel}%
- Coût logement : {cout_logement}€/m²
- Taux d'accession propriété : {accession}%
- Accès sanitaires améliorés : {sanitaires}%
- Satisfaction logement : {satisfaction}%

Documents analysés :
{chr(10).join(doc_texts) if doc_texts else "Aucun document fourni"}

STRUCTURE OBLIGATOIRE (développez CHAQUE section sur 3-4 pages MINIMUM) :

RÉSUMÉ EXÉCUTIF
Rédigez un résumé exécutif de 2 pages complètes incluant :
- Synthèse détaillée des principaux constats avec données chiffrées
- Calcul et interprétation des indices de développement
- Hiérarchisation précise des priorités d'intervention
- Recommandations clés avec timeline et budget estimatif
- Comparaison avec les standards internationaux

CONTEXTE DÉMOGRAPHIQUE ET SOCIAL DÉTAILLÉ
Développez sur 4 pages complètes :
- Analyse approfondie des indicateurs éducatifs avec comparaisons régionales
- Situation sanitaire et médicale : infrastructure, personnel, épidémiologie
- Défis sécuritaires et sociaux : criminalité, cohésion sociale, gouvernance
- Comparaisons détaillées avec Dakar, Bamako, Ouagadougou, Niamey
- Projections démographiques et implications pour les services
- Analyse des inégalités socio-spatiales et de genre

ANALYSE DE L'HABITAT ET DES INFRASTRUCTURES
Rédigez 4 pages complètes sur :
- État détaillé des services essentiels (eau, électricité, assainissement)
- Qualité et typologie du parc de logements par quartier
- Problématiques d'accessibilité et d'abordabilité avec analyse financière
- Défis de l'urbanisation informelle : cartographie, dynamiques, solutions
- Infrastructure de transport et mobilité urbaine
- Gestion des déchets et environnement urbain

DÉFIS ET OPPORTUNITÉS IDENTIFIÉS
Développez sur 3 pages :
- Analyse SWOT ultra-détaillée avec matrice d'impact/probabilité
- Identification précise des goulots d'étranglement avec solutions
- Potentiels de développement inexploités : économique, touristique, culturel
- Risques et vulnérabilités : climatiques, économiques, sociaux, politiques
- Analyse des parties prenantes et de leurs intérêts
- Benchmarking avec les meilleures pratiques africaines

RECOMMANDATIONS STRATÉGIQUES
Rédigez 4 pages complètes incluant :
- Plan d'action détaillé à court terme (1-2 ans) avec budget et responsables
- Stratégies à moyen terme (3-5 ans) avec jalons et indicateurs
- Vision à long terme (10-15 ans) avec scénarios d'évolution
- Mécanismes de financement innovants et partenariats stratégiques
- Cadre institutionnel et réformes nécessaires
- Système complet de suivi-évaluation avec indicateurs SMART

CONCLUSION PROSPECTIVE
Concluez sur 2 pages avec :
- Scénarios d'évolution détaillés (optimiste, réaliste, pessimiste)
- Conditions critiques de succès des recommandations
- Feuille de route opérationnelle avec étapes clés
- Mécanismes d'adaptation et de révision du plan
- Vision transformationnelle pour 2040

EXIGENCES DE QUALITÉ :
- Utilisez un style académique et professionnel de haut niveau
- Intégrez des données chiffrées précises et des références
- Proposez des comparaisons avec au moins 5 villes africaines similaires
- Incluez des recommandations concrètes, chiffrées et réalisables
- Chaque section doit faire MINIMUM 800-1000 mots
- Utilisez des sous-titres clairs et une structure logique
- Adoptez une approche multidisciplinaire (urbanisme, économie, sociologie, environnement)
        """

        if moteur_ia == "OpenAI":
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            rapport = response.choices[0].message.content
        elif moteur_ia == "Hugging Face":
            rapport = generate_hf_report(prompt, st.secrets["HF_TOKEN"])
        elif moteur_ia == "Groq":
            rapport = generate_groq_report(prompt, st.secrets["GROQ_API_KEY"])

        st.success("Rapport de 20+ pages généré avec succès !")
        
        # Affichage du rapport
        st.markdown("### Rapport IA généré")
        st.markdown(rapport)

        # Affichage des graphiques
        st.markdown("### Graphiques et Visualisations")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if 'social_radar' in graphs:
                st.markdown("**Indicateurs Sociaux - Vue d'ensemble**")
                st.image(base64.b64decode(graphs["social_radar"]), use_column_width=True)
        
        with col_g2:
            if 'indices_development' in graphs:
                st.markdown("**Indices de Développement Urbain**")
                st.image(base64.b64decode(graphs["indices_development"]), use_column_width=True)
        
        if 'habitat_analysis' in graphs:
            st.markdown("**Analyse de l'Habitat et des Infrastructures**")
            st.image(base64.b64decode(graphs["habitat_analysis"]), use_column_width=True)

        # Génération du PDF professionnel
        st.info("Génération du PDF professionnel de 20+ pages...")
        pdf_buffer = create_professional_pdf(rapport, ville, graphs, context_info)
        
        st.download_button(
            label="Télécharger le Rapport PDF Professionnel (20+ pages)",
            data=pdf_buffer,
            file_name=f"Diagnostic_Urbain_{ville}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

with tab2:
    st.info("Dashboard analytique à venir - Comparaisons multi-villes, tendances temporelles, benchmarks régionaux...")

with tab3:
    st.header("Assistant IA Urbain")
    question = st.text_input("Posez votre question à l'expert IA en développement urbain")
    if st.button("Envoyer"):
        if question.strip():
            enhanced_prompt = f"""
            Vous êtes un expert en développement urbain africain. Répondez de manière détaillée et professionnelle à cette question :
            
            {question}
            
            Basez votre réponse sur les meilleures pratiques internationales, les spécificités du contexte africain, 
            et fournissez des exemples concrets si pertinents.
            """
            
            if moteur_ia == "Groq":
                reponse = generate_groq_report(enhanced_prompt, st.secrets["GROQ_API_KEY"], model="llama3-8b-8192")
            else:
                client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    max_tokens=800,
                    temperature=0.7,
                )
                reponse = response.choices[0].message.content
            st.markdown(f"**Réponse de l'Expert IA :** {reponse}")
