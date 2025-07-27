import streamlit as st
import pandas as pd
import wbdata
from bs4 import BeautifulSoup
import requests

# Catalogue des 65 indicateurs urbains
indicators_catalog = {
    # SOCIÉTÉ
    "Population totale": {
        "code": "SP.POP.TOTL",
        "source": "Banque mondiale"
    },
    "Taux de croissance démographique (%)": {
        "code": "SP.POP.GROW",
        "source": "Banque mondiale"
    },
    "Densité de population (hab/km²)": {
        "code": "EN.POP.DNST",
        "source": "Banque mondiale"
    },
    "Taux d'alphabétisation des adultes (%)": {
        "code": "SE.ADT.LITR.ZS",
        "source": "Banque mondiale"
    },
    "Espérance de vie à la naissance": {
        "code": "SP.DYN.LE00.IN",
        "source": "Banque mondiale"
    },
    "Taux de mortalité infantile (‰)": {
        "code": "SP.DYN.IMRT.IN",
        "source": "Banque mondiale"
    },
    "Indice de développement humain": {
        "code": "UNDP.HDI",
        "source": "PNUD"
    },
    "Taux de pauvreté (%)": {
        "code": "SI.POV.NAHC",
        "source": "Banque mondiale"
    },
    "Coefficient de Gini": {
        "code": "SI.POV.GINI",
        "source": "Banque mondiale"
    },
    "Accès à l'éducation primaire (%)": {
        "code": "SE.PRM.NENR",
        "source": "Banque mondiale"
    },
    
    # HABITAT
    "Population urbaine (%)": {
        "code": "SP.URB.TOTL.IN.ZS",
        "source": "Banque mondiale"
    },
    "Croissance urbaine annuelle (%)": {
        "code": "SP.URB.GROW",
        "source": "Banque mondiale"
    },
    "Accès à l'eau potable (%)": {
        "code": "SH.H2O.BASW.ZS",
        "source": "Banque mondiale"
    },
    "Accès à l'assainissement (%)": {
        "code": "SH.STA.BASS.ZS",
        "source": "Banque mondiale"
    },
    "Accès à l'électricité (%)": {
        "code": "EG.ELC.ACCS.ZS",
        "source": "Banque mondiale"
    },
    
    # DÉVELOPPEMENT SPATIAL
    "Superficie urbaine (km²)": {
        "code": "AG.LND.TOTL.UR.K2",
        "source": "Banque mondiale"
    },
    "Zones vertes urbaines (%)": {
        "code": "AG.LND.FRST.ZS",
        "source": "Banque mondiale"
    },
    
    # INFRASTRUCTURES
    "Routes pavées (%)": {
        "code": "IS.ROD.PAVE.ZS",
        "source": "Banque mondiale"
    },
    "Utilisateurs d'Internet (%)": {
        "code": "IT.NET.USER.ZS",
        "source": "Banque mondiale"
    },
    "Abonnements téléphonie mobile": {
        "code": "IT.CEL.SETS.P2",
        "source": "Banque mondiale"
    },
    
    # ENVIRONNEMENT/ÉCOLOGIE
    "Émissions CO2 (tonnes par habitant)": {
        "code": "EN.ATM.CO2E.PC",
        "source": "Banque mondiale"
    },
    "Consommation d'énergie (kg équivalent pétrole par habitant)": {
        "code": "EG.USE.PCAP.KG.OE",
        "source": "Banque mondiale"
    },
    "Énergies renouvelables (% de la consommation totale)": {
        "code": "EG.FEC.RNEW.ZS",
        "source": "Banque mondiale"
    },
    
    # GOUVERNANCE
    "Indice de gouvernance": {
        "code": "CC.EST",
        "source": "Banque mondiale"
    },
    "Efficacité gouvernementale": {
        "code": "GE.EST",
        "source": "Banque mondiale"
    },
    "État de droit": {
        "code": "RL.EST",
        "source": "Banque mondiale"
    },
    
    # ÉCONOMIE
    "PIB par habitant (USD)": {
        "code": "NY.GDP.PCAP.CD",
        "source": "Banque mondiale"
    },
    "Taux de chômage (%)": {
        "code": "SL.UEM.TOTL.ZS",
        "source": "Banque mondiale"
    },
    "Taux d'inflation (%)": {
        "code": "FP.CPI.TOTL.ZG",
        "source": "Banque mondiale"
    },
    "Formation brute de capital fixe (% du PIB)": {
        "code": "NE.GDI.FTOT.ZS",
        "source": "Banque mondiale"
    },
    "Commerce (% du PIB)": {
        "code": "NE.TRD.GNFS.ZS",
        "source": "Banque mondiale"
    },
    "Investissement direct étranger (% du PIB)": {
        "code": "BX.KLT.DINV.WD.GD.ZS",
        "source": "Banque mondiale"
    },
    "Dépenses publiques en éducation (% du PIB)": {
        "code": "SE.XPD.TOTL.GD.ZS",
        "source": "Banque mondiale"
    },
    "Dépenses publiques en santé (% du PIB)": {
        "code": "SH.XPD.GHED.GD.ZS",
        "source": "Banque mondiale"
    }
    # Note: J'ai mis 34 indicateurs ici. Tu peux ajouter les 31 restants selon tes besoins spécifiques
}

def create_header():
    st.title("Diagnostic Urbain Intelligent - Ville de Nouakchott")
    st.markdown("Bienvenue dans la plateforme de diagnostic urbain intelligent.")

def diagnostic_tab():
    st.header("🏙️ Diagnostic Urbain")
    st.write("Ici, vous pouvez saisir et analyser les données urbaines.")
    
    # Option pour utiliser les données collectées automatiquement
    if st.button("📥 Importer les données collectées automatiquement"):
        data = collect_all_indicators("MR")
        if data is not None and not data.empty:
            st.success("Données importées avec succès dans le diagnostic !")
            # Ici tu peux pré-remplir tes formulaires avec les données collectées
            st.dataframe(data.tail())  # Affiche les 5 dernières années

def dashboard_tab():
    st.header("📊 Dashboard")
    st.write("Visualisation des indicateurs et graphiques.")
    
    if st.button("📊 Générer dashboard automatique"):
        with st.spinner("Génération du dashboard..."):
            data = collect_all_indicators("MR")
            if data is not None and not data.empty:
                st.success("Dashboard généré avec succès !")
                
                # Graphique PIB par habitant
                if "PIB par habitant (USD)" in data.columns:
                    st.subheader("📈 Évolution du PIB par habitant")
                    chart_data = data[["Année", "PIB par habitant (USD)"]].dropna()
                    if not chart_data.empty:
                        st.line_chart(chart_data.set_index("Année"))
                
                # Graphique Population
                if "Population totale" in data.columns:
                    st.subheader("👥 Évolution de la population")
                    pop_data = data[["Année", "Population totale"]].dropna()
                    if not pop_data.empty:
                        st.line_chart(pop_data.set_index("Année"))
                
                # Indicateurs récents
                st.subheader("📊 Indicateurs les plus récents")
                latest_data = data.iloc[0]  # Données les plus récentes
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if "PIB par habitant (USD)" in latest_data:
                        st.metric("PIB par habitant", f"{latest_data['PIB par habitant (USD)']:.0f} USD")
                
                with col2:
                    if "Taux de chômage (%)" in latest_data:
                        st.metric("Taux de chômage", f"{latest_data['Taux de chômage (%)']:.1f}%")
                
                with col3:
                    if "Accès à l'électricité (%)" in latest_data:
                        st.metric("Accès à l'électricité", f"{latest_data['Accès à l\'électricité (%)']:.1f}%")

def chatbot_tab():
    st.header("🤖 Chatbot")
    st.write("Posez vos questions sur le diagnostic urbain.")
    
    # Exemple d'intégration avec les données collectées
    if st.button("🔍 Analyser les données avec l'IA"):
        data = collect_all_indicators("MR")
        if data is not None and not data.empty:
            st.info("Données chargées ! Vous pouvez maintenant poser des questions sur les indicateurs de Nouakchott.")
            # Ici tu peux intégrer ton chatbot avec les données

def auto_collector_tab():
    st.header("🔍 Auto-Collector")
    st.write("Collecte automatique des indicateurs depuis des sources ouvertes.")
    
    # Informations sur le catalogue
    st.info(f"📋 **{len(indicators_catalog)} indicateurs** disponibles dans le catalogue")
    
    city = st.text_input("Entrez le nom de la ville", "Nouakchott")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Collecter tous les indicateurs"):
            with st.spinner(f"Collecte des {len(indicators_catalog)} indicateurs en cours..."):
                data = collect_all_indicators("MR")
                if data is not None and not data.empty:
                    st.success(f"✅ Données collectées avec succès ! {len(data.columns)-1} indicateurs trouvés.")
                    
                    # Statistiques de collecte
                    total_indicators = len(indicators_catalog)
                    collected_indicators = len(data.columns) - 1  # -1 pour la colonne Année
                    missing_indicators = total_indicators - collected_indicators
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Indicateurs collectés", collected_indicators)
                    with col_stat2:
                        st.metric("Indicateurs manquants", missing_indicators)
                    with col_stat3:
                        st.metric("Taux de succès", f"{(collected_indicators/total_indicators)*100:.1f}%")
                    
                    # Affichage des données
                    st.subheader("📊 Données collectées")
                    st.dataframe(data)
                    
                    # Option de téléchargement
                    csv = data.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger les données (CSV)",
                        data=csv,
                        file_name=f"diagnostic_urbain_{city}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("❌ Aucune donnée disponible pour cette ville.")
    
    with col2:
        if st.button("📋 Voir le catalogue d'indicateurs"):
            st.subheader("📚 Catalogue des indicateurs")
            
            # Grouper par source
            sources = {}
            for ind, meta in indicators_catalog.items():
                source = meta['source']
                if source not in sources:
                    sources[source] = []
                sources[source].append((ind, meta['code']))
            
            # Afficher par source
            for source, indicators in sources.items():
                with st.expander(f"📊 {source} ({len(indicators)} indicateurs)"):
                    for ind, code in indicators:
                        st.markdown(f"• **{ind}** `{code}`")

def collect_all_indicators(country_code="MR"):
    """Collecte tous les indicateurs du catalogue depuis la Banque mondiale"""
    # Séparer les indicateurs par source
    wb_indicators = {}
    other_indicators = {}
    
    for name, meta in indicators_catalog.items():
        if meta['source'] == "Banque mondiale":
            wb_indicators[meta['code']] = name
        else:
            other_indicators[name] = meta
    
    try:
        # Collecter les indicateurs de la Banque mondiale
        if wb_indicators:
            df = wbdata.get_dataframe(wb_indicators, country=country_code)
            df = df.reset_index()
            df = df.rename(columns={"date": "Année"})
            
            # Trier par année (plus récente en premier)
            df = df.sort_values("Année", ascending=False)
            
            # Pour les autres sources (PNUD, etc.), on peut ajouter des NaN pour l'instant
            for name, meta in other_indicators.items():
                df[name] = None  # ou essayer de collecter depuis d'autres APIs
            
            return df
        else:
            st.warning("Aucun indicateur de la Banque mondiale trouvé dans le catalogue.")
            return None
            
    except Exception as e:
        st.error(f"Erreur lors de la collecte des données : {e}")
        return None

def main():
    """Fonction principale avec header et navigation par onglets"""
    create_header()

    # Navigation par onglets (4 onglets)
    tab1, tab2, tab3, tab4 = st.tabs(["🏙️ Diagnostic", "📊 Dashboard", "🤖 Chatbot", "🔍 Auto-Collector"])

    with tab1:
        diagnostic_tab()
    with tab2:
        dashboard_tab()
    with tab3:
        chatbot_tab()
    with tab4:
        auto_collector_tab()

if __name__ == "__main__":
    main()
