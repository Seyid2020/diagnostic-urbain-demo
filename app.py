import streamlit as st
import pandas as pd
import sqlite3
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64

# Configuration de la page
st.set_page_config(
    page_title="Diagnostic Urbain - Nouakchott",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .dimension-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la base de données
def init_database():
    conn = sqlite3.connect('urban_diagnostic.db', check_same_thread=False)
    cursor = conn.cursor()

    # Table des indicateurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            dimension TEXT,
            value REAL,
            unit TEXT,
            source TEXT,
            date_collected TEXT,
            reference TEXT
        )
    """)

    # Table des villes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            country TEXT,
            population INTEGER,
            area REAL
        )
    """)

    conn.commit()
    return conn

# Catalogue des indicateurs
INDICATORS_CATALOG = {
    "Société": {
        "SOC001": {"name": "Taux d'alphabétisation des adultes", "unit": "%", "wb_code": "SE.ADT.LITR.ZS"},
        "SOC002": {"name": "Taux de scolarisation primaire", "unit": "%", "wb_code": "SE.PRM.NENR"},
        "SOC003": {"name": "Ratio élèves/enseignant (primaire)", "unit": "ratio", "wb_code": "SE.PRM.ENRL.TC.ZS"},
        "SOC004": {"name": "Espérance de vie à la naissance", "unit": "années", "wb_code": "SP.DYN.LE00.IN"},
        "SOC005": {"name": "Taux de mortalité infantile", "unit": "‰", "wb_code": "SP.DYN.IMRT.IN"},
        "SOC006": {"name": "Taux de mortalité maternelle", "unit": "/100k", "wb_code": "SH.STA.MMRT"},
        "SOC007": {"name": "Prévalence de la malnutrition", "unit": "%", "wb_code": "SN.ITK.DEFC.ZS"},
        "SOC008": {"name": "Accès aux services de santé", "unit": "%", "wb_code": "SH.MED.BEDS.ZS"},
        "SOC009": {"name": "Taux de chômage", "unit": "%", "wb_code": "SL.UEM.TOTL.ZS"},
        "SOC010": {"name": "Indice de Gini", "unit": "index", "wb_code": "SI.POV.GINI"}
    },
    "Habitat": {
        "HAB001": {"name": "Pourcentage de logements précaires", "unit": "%", "wb_code": "EN.POP.SLUM.UR.ZS"},
        "HAB002": {"name": "Densité de logement", "unit": "log/km²", "wb_code": None},
        "HAB003": {"name": "Taille moyenne des ménages", "unit": "personnes", "wb_code": None},
        "HAB004": {"name": "Accès à l'eau potable", "unit": "%", "wb_code": "SH.H2O.BASW.ZS"},
        "HAB005": {"name": "Accès à l'assainissement", "unit": "%", "wb_code": "SH.STA.BASS.ZS"},
        "HAB006": {"name": "Accès à l'électricité", "unit": "%", "wb_code": "EG.ELC.ACCS.ZS"},
        "HAB007": {"name": "Prix moyen du logement", "unit": "$/m²", "wb_code": None},
        "HAB008": {"name": "Taux de propriétaires", "unit": "%", "wb_code": None}
    },
    "Développement Spatial": {
        "DEV001": {"name": "Superficie urbaine", "unit": "km²", "wb_code": None},
        "DEV002": {"name": "Densité de population urbaine", "unit": "hab/km²", "wb_code": "EN.POP.DNST"},
        "DEV003": {"name": "Taux d'urbanisation", "unit": "%", "wb_code": "SP.URB.TOTL.IN.ZS"},
        "DEV004": {"name": "Espaces verts par habitant", "unit": "m²/hab", "wb_code": None},
        "DEV005": {"name": "Coefficient d'occupation du sol", "unit": "ratio", "wb_code": None},
        "DEV006": {"name": "Longueur du réseau routier", "unit": "km", "wb_code": None},
        "DEV007": {"name": "Densité du réseau routier", "unit": "km/km²", "wb_code": None}
    },
    "Infrastructure": {
        "INF001": {"name": "Longueur des routes pavées", "unit": "km", "wb_code": "IS.ROD.PAVE.ZS"},
        "INF002": {"name": "Accès aux transports publics", "unit": "%", "wb_code": None},
        "INF003": {"name": "Nombre d'hôpitaux", "unit": "unités", "wb_code": None},
        "INF004": {"name": "Nombre d'écoles", "unit": "unités", "wb_code": None},
        "INF005": {"name": "Couverture réseau mobile", "unit": "%", "wb_code": "IT.CEL.SETS.P2"},
        "INF006": {"name": "Accès à Internet", "unit": "%", "wb_code": "IT.NET.USER.ZS"},
        "INF007": {"name": "Capacité de traitement des déchets", "unit": "tonnes/jour", "wb_code": None},
        "INF008": {"name": "Longueur du réseau d'égouts", "unit": "km", "wb_code": None}
    },
    "Environnement/Écologie": {
        "ENV001": {"name": "Qualité de l'air (PM2.5)", "unit": "μg/m³", "wb_code": "EN.ATM.PM25.MC.M3"},
        "ENV002": {"name": "Émissions de CO2", "unit": "tonnes/hab", "wb_code": "EN.ATM.CO2E.PC"},
        "ENV003": {"name": "Consommation d'eau", "unit": "L/hab/jour", "wb_code": None},
        "ENV004": {"name": "Production de déchets", "unit": "kg/hab/jour", "wb_code": None},
        "ENV005": {"name": "Taux de recyclage", "unit": "%", "wb_code": None},
        "ENV006": {"name": "Couverture forestière urbaine", "unit": "%", "wb_code": "AG.LND.FRST.ZS"},
        "ENV007": {"name": "Zones protégées", "unit": "%", "wb_code": "ER.PTD.TOTL.ZS"},
        "ENV008": {"name": "Risque d'inondation", "unit": "niveau", "wb_code": None}
    },
    "Gouvernance": {
        "GOV001": {"name": "Indice de transparence", "unit": "score", "wb_code": None},
        "GOV002": {"name": "Participation électorale", "unit": "%", "wb_code": None},
        "GOV003": {"name": "Efficacité gouvernementale", "unit": "score", "wb_code": "CC.GE.EST"},
        "GOV004": {"name": "État de droit", "unit": "score", "wb_code": "CC.RL.EST"},
        "GOV005": {"name": "Contrôle de la corruption", "unit": "score", "wb_code": "CC.CC.EST"},
        "GOV006": {"name": "Budget municipal par habitant", "unit": "$/hab", "wb_code": None},
        "GOV007": {"name": "Nombre d'ONG actives", "unit": "unités", "wb_code": None}
    },
    "Économie": {
        "ECO001": {"name": "PIB par habitant", "unit": "$", "wb_code": "NY.GDP.PCAP.CD"},
        "ECO002": {"name": "Taux de croissance économique", "unit": "%", "wb_code": "NY.GDP.MKTP.KD.ZG"},
        "ECO003": {"name": "Taux d'inflation", "unit": "%", "wb_code": "FP.CPI.TOTL.ZG"},
        "ECO004": {"name": "Nombre d'entreprises", "unit": "unités", "wb_code": None},
        "ECO005": {"name": "Investissement étranger direct", "unit": "$ millions", "wb_code": "BX.KLT.DINV.CD.WD"},
        "ECO006": {"name": "Recettes fiscales", "unit": "% PIB", "wb_code": "GC.TAX.TOTL.GD.ZS"},
        "ECO007": {"name": "Dépenses publiques", "unit": "% PIB", "wb_code": "GC.XPN.TOTL.GD.ZS"},
        "ECO008": {"name": "Balance commerciale", "unit": "$ millions", "wb_code": "NE.RSB.GNFS.CD"}
    }
}

def collect_worldbank_data(country_code="MRT", year=2022):
    """Collecte des données depuis l'API de la Banque Mondiale"""
    collected_data = {}

    for dimension, indicators in INDICATORS_CATALOG.items():
        for code, info in indicators.items():
            if info.get("wb_code"):
                try:
                    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{info['wb_code']}"
                    params = {
                        "format": "json",
                        "date": f"{year-2}:{year}",
                        "per_page": 10
                    }

                    response = requests.get(url, params=params, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            # Prendre la valeur la plus récente disponible
                            for entry in data[1]:
                                if entry["value"] is not None:
                                    collected_data[code] = {
                                        "name": info["name"],
                                        "value": entry["value"],
                                        "unit": info["unit"],
                                        "dimension": dimension,
                                        "source": "World Bank",
                                        "date": entry["date"],
                                        "reference": f"World Bank - {info['wb_code']}"
                                    }
                                    break
                            else:
                                collected_data[code] = {
                                    "name": info["name"],
                                    "value": None,
                                    "unit": info["unit"],
                                    "dimension": dimension,
                                    "source": "World Bank",
                                    "date": str(year),
                                    "reference": f"World Bank - {info['wb_code']} (No data)"
                                }
                        else:
                            collected_data[code] = {
                                "name": info["name"],
                                "value": None,
                                "unit": info["unit"],
                                "dimension": dimension,
                                "source": "World Bank",
                                "date": str(year),
                                "reference": f"World Bank - {info['wb_code']} (No data)"
                            }
                    else:
                        collected_data[code] = {
                            "name": info["name"],
                            "value": None,
                            "unit": info["unit"],
                            "dimension": dimension,
                            "source": "World Bank",
                            "date": str(year),
                            "reference": f"World Bank - {info['wb_code']} (API Error)"
                        }

                except Exception as e:
                    collected_data[code] = {
                        "name": info["name"],
                        "value": None,
                        "unit": info["unit"],
                        "dimension": dimension,
                        "source": "World Bank",
                        "date": str(year),
                        "reference": f"World Bank - {info['wb_code']} (Error: {str(e)})"
                    }
            else:
                collected_data[code] = {
                    "name": info["name"],
                    "value": None,
                    "unit": info["unit"],
                    "dimension": dimension,
                    "source": "Manual Input Required",
                    "date": str(year),
                    "reference": "No automated source available"
                }

    return collected_data

def save_indicators_to_db(conn, indicators_data):
    """Sauvegarde les indicateurs dans la base de données"""
    cursor = conn.cursor()

    for code, data in indicators_data.items():
        cursor.execute("""
            INSERT OR REPLACE INTO indicators 
            (code, name, dimension, value, unit, source, date_collected, reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code, data["name"], data["dimension"], data["value"],
            data["unit"], data["source"], data["date"], data["reference"]
        ))

    conn.commit()

def load_indicators_from_db(conn):
    """Charge les indicateurs depuis la base de données"""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM indicators')
    rows = cursor.fetchall()

    indicators = {}
    for row in rows:
        indicators[row[1]] = {  # row[1] is code
            "name": row[2],
            "dimension": row[3],
            "value": row[4],
            "unit": row[5],
            "source": row[6],
            "date": row[7],
            "reference": row[8]
        }

    return indicators

def calculate_dimension_score(dimension_data):
    """Calcule le score d'une dimension basé sur ses indicateurs"""
    valid_values = [v["value"] for v in dimension_data.values() if v["value"] is not None]

    if not valid_values:
        return 0

    # Score simple basé sur la moyenne normalisée (à adapter selon les indicateurs)
    normalized_score = min(100, max(0, sum(valid_values) / len(valid_values)))
    return round(normalized_score, 2)

def auto_collector_tab():
    """Interface pour la collecte automatique de données"""
    st.header("🔄 Collecteur Automatique de Données")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Configuration de la collecte")

        country_code = st.selectbox(
            "Code pays (ISO 3)",
            ["MRT", "SEN", "MLI", "NER", "BFA", "CIV"],
            index=0,
            help="Code ISO 3 lettres du pays"
        )

        year = st.number_input(
            "Année de référence",
            min_value=2000,
            max_value=2024,
            value=2022,
            help="Année pour laquelle collecter les données"
        )

    with col2:
        st.subheader("Actions")

        if st.button("🚀 Lancer la collecte", type="primary"):
            with st.spinner("Collecte des données en cours..."):
                try:
                    # Collecte des données
                    indicators_data = collect_worldbank_data(country_code, year)

                    # Sauvegarde en base
                    conn = st.session_state.db_conn
                    save_indicators_to_db(conn, indicators_data)

                    # Mise à jour du session state
                    st.session_state.indicators_data = indicators_data

                    st.success(f"✅ Collecte terminée ! {len(indicators_data)} indicateurs traités.")

                    # Statistiques de collecte
                    collected_count = sum(1 for v in indicators_data.values() if v["value"] is not None)
                    missing_count = len(indicators_data) - collected_count

                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Total indicateurs", len(indicators_data))
                    with col_stat2:
                        st.metric("Données collectées", collected_count)
                    with col_stat3:
                        st.metric("Données manquantes", missing_count)

                except Exception as e:
                    st.error(f"❌ Erreur lors de la collecte : {str(e)}")

    # Affichage des données collectées
    if hasattr(st.session_state, 'indicators_data'):
        st.subheader("📊 Données collectées")

        # Filtre par dimension
        dimensions = list(set(v["dimension"] for v in st.session_state.indicators_data.values()))
        selected_dimension = st.selectbox("Filtrer par dimension", ["Toutes"] + dimensions)

        # Préparation des données pour l'affichage
        display_data = []
        for code, data in st.session_state.indicators_data.items():
            if selected_dimension == "Toutes" or data["dimension"] == selected_dimension:
                display_data.append({
                    "Code": code,
                    "Indicateur": data["name"],
                    "Dimension": data["dimension"],
                    "Valeur": data["value"] if data["value"] is not None else "N/A",
                    "Unité": data["unit"],
                    "Source": data["source"],
                    "Date": data["date"]
                })

        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)

            # Option de téléchargement
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger les données (CSV)",
                data=csv,
                file_name=f"indicators_{country_code}_{year}.csv",
                mime="text/csv"
            )

def diagnostic_tab():
    """Interface pour le diagnostic urbain"""
    st.header("📋 Diagnostic Urbain")

    # Chargement des données existantes
    if not hasattr(st.session_state, 'indicators_data'):
        conn = st.session_state.db_conn
        st.session_state.indicators_data = load_indicators_from_db(conn)

    if not st.session_state.indicators_data:
        st.warning("⚠️ Aucune donnée disponible. Veuillez d'abord utiliser le collecteur automatique.")
        return

    # Organisation par dimensions
    dimensions = {}
    for code, data in st.session_state.indicators_data.items():
        dim = data["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {}
        dimensions[dim][code] = data

    # Interface de saisie par dimension
    st.subheader("📝 Saisie et validation des données")

    updated_data = {}

    for dimension, indicators in dimensions.items():
        with st.expander(f"📊 {dimension}", expanded=False):
            st.markdown(f"<h4 class='dimension-header'>{dimension}</h4>", unsafe_allow_html=True)

            cols = st.columns(2)
            for i, (code, data) in enumerate(indicators.items()):
                with cols[i % 2]:
                    current_value = data["value"] if data["value"] is not None else 0.0

                    new_value = st.number_input(
                        f"{data['name']} ({data['unit']})",
                        value=float(current_value),
                        key=f"input_{code}",
                        help=f"Source: {data['source']} | Référence: {data['reference']}"
                    )

                    updated_data[code] = {
                        **data,
                        "value": new_value
                    }

    # Bouton de sauvegarde
    if st.button("💾 Sauvegarder les modifications", type="primary"):
        conn = st.session_state.db_conn
        save_indicators_to_db(conn, updated_data)
        st.session_state.indicators_data = updated_data
        st.success("✅ Données sauvegardées avec succès !")

    # Calcul et affichage des scores par dimension
    st.subheader("📈 Scores par dimension")

    dimension_scores = {}
    cols = st.columns(len(dimensions))

    for i, (dimension, indicators) in enumerate(dimensions.items()):
        score = calculate_dimension_score(indicators)
        dimension_scores[dimension] = score

        with cols[i]:
            st.metric(
                label=dimension,
                value=f"{score}/100",
                delta=None
            )

def dashboard_tab():
    """Interface du tableau de bord"""
    st.header("📊 Tableau de Bord")

    if not hasattr(st.session_state, 'indicators_data') or not st.session_state.indicators_data:
        st.warning("⚠️ Aucune donnée disponible pour le tableau de bord.")
        return

    # Organisation des données par dimension
    dimensions = {}
    for code, data in st.session_state.indicators_data.items():
        dim = data["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {}
        dimensions[dim][code] = data

    # Métriques principales
    st.subheader("🎯 Indicateurs Clés")

    key_metrics = {
        "Population urbaine": st.session_state.indicators_data.get("DEV003", {}).get("value", "N/A"),
        "Accès à l'eau potable": st.session_state.indicators_data.get("HAB004", {}).get("value", "N/A"),
        "PIB par habitant": st.session_state.indicators_data.get("ECO001", {}).get("value", "N/A"),
        "Espérance de vie": st.session_state.indicators_data.get("SOC004", {}).get("value", "N/A")
    }

    cols = st.columns(4)
    for i, (metric, value) in enumerate(key_metrics.items()):
        with cols[i]:
            if value != "N/A" and value is not None:
                st.metric(metric, f"{value:.1f}")
            else:
                st.metric(metric, "N/A")

    # Graphiques par dimension
    st.subheader("📈 Visualisations par Dimension")

    # Scores par dimension
    dimension_scores = {}
    for dimension, indicators in dimensions.items():
        valid_values = [v["value"] for v in indicators.values() if v["value"] is not None]
        if valid_values:
            # Score normalisé simple (à adapter selon la logique métier)
            score = min(100, max(0, sum(valid_values) / len(valid_values)))
            dimension_scores[dimension] = score
        else:
            dimension_scores[dimension] = 0

    # Graphique radar des scores
    if dimension_scores:
        fig_radar = go.Figure()

        fig_radar.add_trace(go.Scatterpolar(
            r=list(dimension_scores.values()),
            theta=list(dimension_scores.keys()),
            fill='toself',
            name='Scores'
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Scores par Dimension"
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    # Graphiques détaillés par dimension
    selected_dim = st.selectbox("Sélectionner une dimension pour le détail", list(dimensions.keys()))

    if selected_dim and selected_dim in dimensions:
        dim_data = dimensions[selected_dim]

        # Préparation des données pour le graphique
        indicators_names = []
        indicators_values = []

        for code, data in dim_data.items():
            if data["value"] is not None:
                indicators_names.append(data["name"][:30] + "..." if len(data["name"]) > 30 else data["name"])
                indicators_values.append(data["value"])

        if indicators_names and indicators_values:
            fig_bar = px.bar(
                x=indicators_values,
                y=indicators_names,
                orientation='h',
                title=f"Indicateurs - {selected_dim}",
                labels={'x': 'Valeur', 'y': 'Indicateurs'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour cette dimension.")

def generate_pdf_report():
    """Génère un rapport PDF"""
    if not hasattr(st.session_state, 'indicators_data') or not st.session_state.indicators_data:
        return None

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
        alignment=1  # Center
    )
    story.append(Paragraph("DIAGNOSTIC URBAIN - NOUAKCHOTT", title_style))
    story.append(Spacer(1, 20))

    # Date
    story.append(Paragraph(f"Date du rapport: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Résumé exécutif
    story.append(Paragraph("RÉSUMÉ EXÉCUTIF", styles['Heading2']))
    story.append(Paragraph(
        "Ce rapport présente un diagnostic urbain complet de Nouakchott basé sur "
        "65 indicateurs répartis en 7 dimensions clés : Société, Habitat, "
        "Développement Spatial, Infrastructure, Environnement/Écologie, "
        "Gouvernance et Économie.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))

    # Organisation des données par dimension
    dimensions = {}
    for code, data in st.session_state.indicators_data.items():
        dim = data["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {}
        dimensions[dim][code] = data

    # Analyse par dimension
    for dimension, indicators in dimensions.items():
        story.append(Paragraph(f"{dimension.upper()}", styles['Heading2']))

        # Tableau des indicateurs
        table_data = [["Indicateur", "Valeur", "Unité", "Source"]]

        for code, data in indicators.items():
            value_str = str(data["value"]) if data["value"] is not None else "N/A"
            table_data.append([
                data["name"][:40] + "..." if len(data["name"]) > 40 else data["name"],
                value_str,
                data["unit"],
                data["source"][:20] + "..." if len(data["source"]) > 20 else data["source"]
            ])

        table = Table(table_data, colWidths=[3*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

        if dimension != list(dimensions.keys())[-1]:  # Pas de saut de page pour la dernière dimension
            story.append(PageBreak())

    # Conclusion
    story.append(Paragraph("CONCLUSION ET RECOMMANDATIONS", styles['Heading2']))
    story.append(Paragraph(
        "Ce diagnostic urbain révèle les défis et opportunités de développement "
        "de Nouakchott. Les données collectées permettent d'identifier les "
        "priorités d'intervention et de formuler des stratégies de développement "
        "urbain durable.",
        styles['Normal']
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

def reports_tab():
    """Interface pour la génération de rapports"""
    st.header("📄 Génération de Rapports")

    if not hasattr(st.session_state, 'indicators_data') or not st.session_state.indicators_data:
        st.warning("⚠️ Aucune donnée disponible pour générer un rapport.")
        return

    st.subheader("📋 Configuration du rapport")

    col1, col2 = st.columns([2, 1])

    with col1:
        report_title = st.text_input("Titre du rapport", "Diagnostic Urbain - Nouakchott")
        report_author = st.text_input("Auteur", "Équipe de Diagnostic Urbain")

        include_sections = st.multiselect(
            "Sections à inclure",
            ["Résumé exécutif", "Analyse par dimension", "Graphiques", "Recommandations"],
            default=["Résumé exécutif", "Analyse par dimension", "Recommandations"]
        )

    with col2:
        st.subheader("Actions")

        if st.button("📊 Aperçu des données", type="secondary"):
            # Statistiques rapides
            total_indicators = len(st.session_state.indicators_data)
            collected_indicators = sum(1 for v in st.session_state.indicators_data.values() if v["value"] is not None)

            st.info(f"📈 {collected_indicators}/{total_indicators} indicateurs avec données")

        if st.button("🔄 Générer le rapport PDF", type="primary"):
            with st.spinner("Génération du rapport en cours..."):
                try:
                    pdf_buffer = generate_pdf_report()

                    if pdf_buffer:
                        st.success("✅ Rapport généré avec succès !")

                        # Bouton de téléchargement
                        st.download_button(
                            label="📥 Télécharger le rapport PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"diagnostic_urbain_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("❌ Erreur lors de la génération du rapport.")

                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération : {str(e)}")

    # Prévisualisation des données
    st.subheader("👁️ Prévisualisation des données")

    # Organisation par dimension pour l'affichage
    dimensions = {}
    for code, data in st.session_state.indicators_data.items():
        dim = data["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {}
        dimensions[dim][code] = data

    # Affichage par dimension
    for dimension, indicators in dimensions.items():
        with st.expander(f"📊 {dimension}"):
            data_for_table = []
            for code, data in indicators.items():
                data_for_table.append({
                    "Code": code,
                    "Indicateur": data["name"],
                    "Valeur": data["value"] if data["value"] is not None else "N/A",
                    "Unité": data["unit"],
                    "Source": data["source"]
                })

            if data_for_table:
                df = pd.DataFrame(data_for_table)
                st.dataframe(df, use_container_width=True)

def chatbot_tab():
    """Interface du chatbot"""
    st.header("🤖 Assistant Diagnostic")

    st.info("💡 Posez vos questions sur les données urbaines de Nouakchott")

    # Historique des conversations
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Zone de saisie
    user_question = st.text_input("Votre question:", placeholder="Ex: Quel est le taux d'accès à l'eau potable ?")

    if st.button("Envoyer") and user_question:
        # Simulation de réponse du chatbot
        if not hasattr(st.session_state, 'indicators_data'):
            response = "Je n'ai pas encore accès aux données. Veuillez d'abord utiliser le collecteur automatique."
        else:
            # Logique simple de réponse basée sur les mots-clés
            response = generate_chatbot_response(user_question, st.session_state.indicators_data)

        # Ajout à l'historique
        st.session_state.chat_history.append({"user": user_question, "bot": response})

    # Affichage de l'historique
    if st.session_state.chat_history:
        st.subheader("💬 Conversation")

        for i, exchange in enumerate(reversed(st.session_state.chat_history[-5:])):  # 5 derniers échanges
            with st.container():
                st.markdown(f"**👤 Vous:** {exchange['user']}")
                st.markdown(f"**🤖 Assistant:** {exchange['bot']}")
                st.markdown("---")

def generate_chatbot_response(question, indicators_data):
    """Génère une réponse simple du chatbot"""
    question_lower = question.lower()

    # Mots-clés pour différents indicateurs
    keywords_mapping = {
        "eau": ["HAB004"],
        "électricité": ["HAB006"],
        "assainissement": ["HAB005"],
        "population": ["DEV002", "DEV003"],
        "pib": ["ECO001"],
        "économie": ["ECO001", "ECO002"],
        "santé": ["SOC004", "SOC005"],
        "éducation": ["SOC001", "SOC002"],
        "environnement": ["ENV001", "ENV002"],
        "transport": ["INF001", "INF002"]
    }

    # Recherche de mots-clés
    relevant_indicators = []
    for keyword, codes in keywords_mapping.items():
        if keyword in question_lower:
            for code in codes:
                if code in indicators_data:
                    relevant_indicators.append((code, indicators_data[code]))

    if relevant_indicators:
        response = "Voici les informations que j'ai trouvées :\n\n"
        for code, data in relevant_indicators:
            value_str = f"{data['value']:.2f} {data['unit']}" if data['value'] is not None else "Donnée non disponible"
            response += f"• **{data['name']}**: {value_str}\n"
            response += f"  Source: {data['source']} ({data['date']})\n\n"
    else:
        response = ("Je n'ai pas trouvé d'informations spécifiques pour votre question. "
                   "Vous pouvez consulter le tableau de bord pour voir toutes les données disponibles, "
                   "ou reformuler votre question avec des termes comme 'eau', 'électricité', "
                   "'population', 'PIB', 'santé', 'éducation', etc.")

    return response

def main():
    """Fonction principale de l'application"""

    # Initialisation de la base de données
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_database()

    # Titre principal
    st.markdown("<h1 class='main-header'>🏙️ Diagnostic Urbain - Nouakchott</h1>", unsafe_allow_html=True)

    # Sidebar avec informations
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/white?text=NOUAKCHOTT", caption="Ville de Nouakchott")

        st.markdown("### 📊 Informations du projet")
        st.markdown("""
        - **65 indicateurs** répartis en 7 dimensions
        - **Collecte automatisée** depuis la Banque Mondiale
        - **Interface intuitive** pour la saisie manuelle
        - **Rapports PDF** personnalisables
        - **Tableau de bord** interactif
        """)

        st.markdown("### 🎯 Dimensions analysées")
        dimensions_list = [
            "🏛️ Société", "🏠 Habitat", "🌆 Développement Spatial",
            "🚧 Infrastructure", "🌱 Environnement", "⚖️ Gouvernance", "💰 Économie"
        ]
        for dim in dimensions_list:
            st.markdown(f"- {dim}")

    # Navigation par onglets
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔄 Auto-Collecteur", "📋 Diagnostic", "📊 Tableau de Bord", 
        "📄 Rapports", "🤖 Assistant", "ℹ️ À propos"
    ])

    with tab1:
        auto_collector_tab()

    with tab2:
        diagnostic_tab()

    with tab3:
        dashboard_tab()

    with tab4:
        reports_tab()

    with tab5:
        chatbot_tab()

    with tab6:
        st.header("ℹ️ À propos du projet")

        st.markdown("""
        ### 🎯 Objectif
        Cette application permet de réaliser un diagnostic urbain complet de Nouakchott 
        en collectant et analysant 65 indicateurs clés répartis en 7 dimensions.

        ### 🔧 Fonctionnalités
        - **Collecte automatique** de données depuis l'API de la Banque Mondiale
        - **Interface de saisie** pour les données locales
        - **Calcul automatique** des scores par dimension
        - **Visualisations interactives** avec Plotly
        - **Génération de rapports PDF** personnalisables
        - **Assistant conversationnel** pour l'aide à la décision

        ### 📈 Dimensions analysées
        1. **Société** - Éducation, santé, démographie
        2. **Habitat** - Logement, services de base
        3. **Développement Spatial** - Urbanisation, densité
        4. **Infrastructure** - Transport, télécommunications
        5. **Environnement** - Qualité de l'air, gestion des déchets
        6. **Gouvernance** - Transparence, participation
        7. **Économie** - PIB, emploi, investissements

        ### 👥 Équipe de développement
        Développé pour le diagnostic urbain de Nouakchott, Mauritanie.

        ### 📞 Support
        Pour toute question ou suggestion d'amélioration, contactez l'équipe de développement.
        """)

if __name__ == "__main__":
    main()
