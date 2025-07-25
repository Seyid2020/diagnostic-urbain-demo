import streamlit as st
import pandas as pd
import wbdata
from bs4 import BeautifulSoup
import requests

def create_header():
    st.title("Diagnostic Urbain Intelligent - Ville de Nouakchott")
    st.markdown("Bienvenue dans la plateforme de diagnostic urbain intelligent.")

def diagnostic_tab():
    st.header("🏙️ Diagnostic Urbain")
    st.write("Ici, vous pouvez saisir et analyser les données urbaines.")

def dashboard_tab():
    st.header("📊 Dashboard")
    st.write("Visualisation des indicateurs et graphiques.")

def chatbot_tab():
    st.header("🤖 Chatbot")
    st.write("Posez vos questions sur le diagnostic urbain.")

def auto_collector_tab():
    st.header("🔍 Auto-Collector")
    st.write("Collecte automatique des indicateurs depuis des sources ouvertes.")

    city = st.text_input("Entrez le nom de la ville", "Nouakchott")
    if st.button("Collecter les données"):
        with st.spinner("Collecte des données en cours..."):
            data = collect_from_worldbank(city)
            if data is not None and not data.empty:
                st.success("Données collectées avec succès !")
                st.dataframe(data)
            else:
                st.warning("Aucune donnée disponible pour cette ville.")

def collect_from_worldbank(city):
    # Exemple simple : collecte du PIB par habitant pour le pays Mauritanie (code ISO: MRT)
    # En pratique, il faudrait mapper la ville au pays et aux indicateurs pertinents
    country_code = "MR"  # Code ISO 2 lettres pour Mauritanie
    indicators = {"NY.GDP.PCAP.CD": "PIB par habitant (USD)"}
    try:
        df = wbdata.get_dataframe(indicators, country=country_code, convert_date=False)
        df = df.reset_index()
        df = df.rename(columns={"date": "Année"})
        return df
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
