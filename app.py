###############################################################################
# ░█▀▀▀ ░█▀▀▀ ░█▄─░█ ░█▀▀█ 　 Diagnostic Urbain Intelligent
# ░█▀▀▀ ░█▀▀▀ ░█░█░█ ░█─── 　 Plateforme Streamlit – Collecte Auto d'indicateurs
# ░█▄▄▄ ░█▄▄▄ ░█──▀█ ░█▄▄█ 　 (rempli NaN si un indicateur est introuvable)
###############################################################################
import os
os.environ["STREAMLIT_THREADING_MODE"] = "single"   # ← important avec wbdata

import streamlit as st
import pandas as pd
import wbdata
from functools import reduce
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1. CATALOGUE DES INDICATEURS (34 pour l'exemple, extensible à 65)
# ─────────────────────────────────────────────────────────────────────────────
indicators_catalog = {
    # SOCIÉTÉ
    "Population totale":                 {"code": "SP.POP.TOTL",        "source": "Banque mondiale", "dimension": "Société"},
    "Taux de croissance démographique (%)": {"code": "SP.POP.GROW",    "source": "Banque mondiale", "dimension": "Société"},
    "Densité de population (hab/km²)":   {"code": "EN.POP.DNST",        "source": "Banque mondiale", "dimension": "Société"},
    "Taux d'alphabétisation des adultes (%)": {"code": "SE.ADT.LITR.ZS","source": "Banque mondiale", "dimension": "Société"},
    "Espérance de vie à la naissance":   {"code": "SP.DYN.LE00.IN",     "source": "Banque mondiale", "dimension": "Société"},
    "Taux de mortalité infantile (‰)":   {"code": "SP.DYN.IMRT.IN",     "source": "Banque mondiale", "dimension": "Société"},
    "Indice de développement humain":    {"code": "UNDP.HDI",           "source": "PNUD", "dimension": "Société"},
    "Taux de pauvreté (%)":              {"code": "SI.POV.NAHC",        "source": "Banque mondiale", "dimension": "Société"},
    "Coefficient de Gini":              {"code": "SI.POV.GINI",        "source": "Banque mondiale", "dimension": "Société"},
    "Accès à l'éducation primaire (%)":  {"code": "SE.PRM.NENR",        "source": "Banque mondiale", "dimension": "Société"},
    # HABITAT
    "Population urbaine (%)":            {"code": "SP.URB.TOTL.IN.ZS",  "source": "Banque mondiale", "dimension": "Habitat"},
    "Croissance urbaine annuelle (%)":   {"code": "SP.URB.GROW",        "source": "Banque mondiale", "dimension": "Habitat"},
    "Accès à l'eau potable (%)":         {"code": "SH.H2O.BASW.ZS",     "source": "Banque mondiale", "dimension": "Habitat"},
    "Accès à l'assainissement (%)":      {"code": "SH.STA.BASS.ZS",     "source": "Banque mondiale", "dimension": "Habitat"},
    "Accès à l'électricité (%)":         {"code": "EG.ELC.ACCS.ZS",     "source": "Banque mondiale", "dimension": "Habitat"},
    # DÉVELOPPEMENT SPATIAL
    "Superficie urbaine (km²)":          {"code": "AG.LND.TOTL.UR.K2",  "source": "Banque mondiale", "dimension": "Développement Spatial"},
    "Zones vertes urbaines (%)":         {"code": "AG.LND.FRST.ZS",     "source": "Banque mondiale", "dimension": "Développement Spatial"},
    # INFRASTRUCTURES
    "Routes pavées (%)":                 {"code": "IS.ROD.PAVE.ZS",     "source": "Banque mondiale", "dimension": "Infrastructures"},
    "Utilisateurs d'Internet (%)":       {"code": "IT.NET.USER.ZS",     "source": "Banque mondiale", "dimension": "Infrastructures"},
    "Abonnements téléphonie mobile":     {"code": "IT.CEL.SETS.P2",     "source": "Banque mondiale", "dimension": "Infrastructures"},
    # ENVIRONNEMENT
    "Émissions CO2 (t/hab)":             {"code": "EN.ATM.CO2E.PC",     "source": "Banque mondiale", "dimension": "Environnement"},
    "Consommation d'énergie (kg éq. pétrol/hab)": {"code":"EG.USE.PCAP.KG.OE","source":"Banque mondiale", "dimension": "Environnement"},
    "Énergies renouvelables (% conso. totale)":   {"code":"EG.FEC.RNEW.ZS","source":"Banque mondiale", "dimension": "Environnement"},
    # GOUVERNANCE
    "Indice de gouvernance (Voix & Redevabilité)": {"code":"VA.EST","source":"Banque mondiale", "dimension": "Gouvernance"},
    "Efficacité gouvernementale":        {"code": "GE.EST",             "source": "Banque mondiale", "dimension": "Gouvernance"},
    "État de droit":                     {"code": "RL.EST",             "source": "Banque mondiale", "dimension": "Gouvernance"},
    # ÉCONOMIE
    "PIB par habitant (USD)":            {"code": "NY.GDP.PCAP.CD",     "source": "Banque mondiale", "dimension": "Économie"},
    "Taux de chômage (%)":               {"code": "SL.UEM.TOTL.ZS",     "source": "Banque mondiale", "dimension": "Économie"},
    "Taux d'inflation (%)":              {"code": "FP.CPI.TOTL.ZG",     "source": "Banque mondiale", "dimension": "Économie"},
    "Formation brute de capital fixe (% PIB)": {"code":"NE.GDI.FTOT.ZS","source":"Banque mondiale", "dimension": "Économie"},
    "Commerce (% PIB)":                  {"code": "NE.TRD.GNFS.ZS",     "source": "Banque mondiale", "dimension": "Économie"},
    "IDE net entrant (% PIB)":           {"code": "BX.KLT.DINV.WD.GD.ZS","source":"Banque mondiale", "dimension": "Économie"},
    "Dépenses publiques éducation (% PIB)": {"code":"SE.XPD.TOTL.GD.ZS","source":"Banque mondiale", "dimension": "Économie"},
    "Dépenses publiques santé (% PIB)":  {"code": "SH.XPD.GHED.GD.ZS",  "source": "Banque mondiale", "dimension": "Économie"}
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────
def create_header():
    st.title("🏙️ Diagnostic Urbain Intelligent - Ville de Nouakchott")
    st.markdown("Bienvenue dans la plateforme de diagnostic urbain intelligent.")

# ---------- Collecte robuste (NaN si échec) ----------
def collect_all_indicators(country_code="MR"):
    """
    Tente de récupérer chaque indicateur individuellement.
    Si un code échoue → colonne remplie de NaN.
    Retourne un DataFrame fusionné, indexé par Année (descendant).
    """
    current_year = datetime.now().year
    base_df = pd.DataFrame({"Année": list(range(current_year, 1959, -1))})
    dfs = []

    for ind_name, meta in indicators_catalog.items():
        if meta["source"] != "Banque mondiale":
            tmp = base_df.copy()
            tmp[ind_name] = pd.NA
            dfs.append(tmp)
            continue

        code = meta["code"]
        try:
            df = wbdata.get_dataframe({code: ind_name}, country=country_code)
            if df.empty or df[ind_name].isnull().all():
                tmp = base_df.copy()
                tmp[ind_name] = pd.NA
                dfs.append(tmp)
            else:
                df = df.reset_index().rename(columns={"date": "Année"})
                df["Année"] = df["Année"].astype(int)
                tmp = pd.merge(base_df, df, on="Année", how="left")
                dfs.append(tmp[["Année", ind_name]])
        except Exception:
            tmp = base_df.copy()
            tmp[ind_name] = pd.NA
            dfs.append(tmp)

    df_final = base_df.copy()
    for d in dfs:
        df_final = pd.merge(df_final, d, on="Année", how="left")
    df_final = df_final.loc[:,~df_final.columns.duplicated()]
    df_final.sort_values("Année", ascending=False, inplace=True)
    return df_final

def calculate_dimension_score(data, dimension):
    """Calcule le score d'une dimension basé sur ses indicateurs"""
    dimension_indicators = [ind for ind, meta in indicators_catalog.items() 
                          if meta.get("dimension") == dimension]
    
    if not dimension_indicators:
        return 0
    
    latest_data = data.iloc[0] if not data.empty else pd.Series()
    scores = []
    
    for ind in dimension_indicators:
        if ind in latest_data and pd.notna(latest_data[ind]):
            # Normalisation simple (à adapter selon l'indicateur)
            value = float(latest_data[ind])
            if "taux" in ind.lower() and "chômage" in ind.lower():
                # Pour le chômage, plus c'est bas, mieux c'est
                normalized = max(0, 100 - value) / 100
            elif "mortalité" in ind.lower():
                # Pour la mortalité, plus c'est bas, mieux c'est
                normalized = max(0, 100 - value) / 100
            else:
                # Pour la plupart des autres indicateurs, plus c'est haut, mieux c'est
                normalized = min(value / 100, 1) if value <= 100 else min(value / 1000, 1)
            scores.append(normalized)
    
    return np.mean(scores) * 100 if scores else 0

# ─────────────────────────────────────────────────────────────────────────────
# 3. ONGLET : DIAGNOSTIC COMPLET
# ─────────────────────────────────────────────────────────────────────────────
def diagnostic_tab():
    st.header("🏙️ Diagnostic Urbain Complet")
    
    # Collecte automatique des données
    if 'diagnostic_data' not in st.session_state:
        st.session_state.diagnostic_data = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Charger les données automatiquement"):
            with st.spinner("Chargement des données..."):
                st.session_state.diagnostic_data = collect_all_indicators("MR")
            st.success("✅ Données chargées avec succès !")
    
    with col2:
        if st.button("🔄 Réinitialiser le diagnostic"):
            st.session_state.diagnostic_data = None
            st.success("Diagnostic réinitialisé")
    
    if st.session_state.diagnostic_data is not None:
        data = st.session_state.diagnostic_data
        latest_data = data.iloc[0] if not data.empty else pd.Series()
        
        # Formulaires par dimension
        dimensions = list(set(meta.get("dimension", "Autre") for meta in indicators_catalog.values()))
        
        st.subheader("📊 Saisie et modification des indicateurs par dimension")
        
        # Stockage des valeurs modifiées
        if 'modified_values' not in st.session_state:
            st.session_state.modified_values = {}
        
        for dimension in sorted(dimensions):
            with st.expander(f"📋 {dimension}"):
                dimension_indicators = [ind for ind, meta in indicators_catalog.items() 
                                      if meta.get("dimension") == dimension]
                
                for ind in dimension_indicators:
                    col_ind1, col_ind2, col_ind3 = st.columns([3, 2, 1])
                    
                    with col_ind1:
                        st.write(f"**{ind}**")
                    
                    with col_ind2:
                        # Valeur automatique
                        auto_value = latest_data.get(ind, None)
                        if pd.notna(auto_value):
                            st.write(f"Auto: {auto_value:.2f}")
                        else:
                            st.write("Auto: N/A")
                    
                    with col_ind3:
                        # Champ de saisie manuelle
                        current_value = st.session_state.modified_values.get(ind, 
                                       auto_value if pd.notna(auto_value) else 0.0)
                        new_value = st.number_input(
                            f"Valeur", 
                            value=float(current_value) if pd.notna(current_value) else 0.0,
                            key=f"input_{ind}",
                            format="%.2f"
                        )
                        st.session_state.modified_values[ind] = new_value
                
                # Score de la dimension
                score = calculate_dimension_score(data, dimension)
                st.metric(f"Score {dimension}", f"{score:.1f}/100")
        
        # Score global
        st.subheader("🎯 Score Global du Diagnostic")
        all_scores = [calculate_dimension_score(data, dim) for dim in dimensions]
        global_score = np.mean([s for s in all_scores if s > 0])
        
        col_score1, col_score2, col_score3 = st.columns(3)
        with col_score1:
            st.metric("Score Global", f"{global_score:.1f}/100")
        with col_score2:
            st.metric("Dimensions évaluées", f"{len([s for s in all_scores if s > 0])}/{len(dimensions)}")
        with col_score3:
            if st.button("📄 Générer rapport"):
                st.success("Rapport généré ! (Fonctionnalité à développer)")

# ─────────────────────────────────────────────────────────────────────────────
# 4. ONGLET : DASHBOARD ENRICHI
# ─────────────────────────────────────────────────────────────────────────────
def dashboard_tab():
    st.header("📊 Dashboard Interactif")
    
    # Collecte des données
    if st.button("🔄 Actualiser les données"):
        with st.spinner("Chargement des données..."):
            data = collect_all_indicators("MR")
            st.session_state.dashboard_data = data
    
    if 'dashboard_data' not in st.session_state:
        st.info("Cliquez sur 'Actualiser les données' pour charger le dashboard")
        return
    
    data = st.session_state.dashboard_data
    latest_data = data.iloc[0] if not data.empty else pd.Series()
    
    # KPI Cards
    st.subheader("📈 Indicateurs Clés")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pib = latest_data.get("PIB par habitant (USD)", 0)
        st.metric("PIB par habitant", f"{pib:.0f} USD" if pd.notna(pib) else "N/A")
    
    with col2:
        pop = latest_data.get("Population totale", 0)
        st.metric("Population", f"{pop/1000000:.1f}M" if pd.notna(pop) else "N/A")
    
    with col3:
        elec = latest_data.get("Accès à l'électricité (%)", 0)
        st.metric("Accès électricité", f"{elec:.1f}%" if pd.notna(elec) else "N/A")
    
    with col4:
        eau = latest_data.get("Accès à l'eau potable (%)", 0)
        st.metric("Accès eau potable", f"{eau:.1f}%" if pd.notna(eau) else "N/A")
    
    # Graphiques par dimension
    st.subheader("📊 Évolution par dimension")
    
    dimensions = list(set(meta.get("dimension", "Autre") for meta in indicators_catalog.values()))
    selected_dimension = st.selectbox("Choisir une dimension", dimensions)
    
    dimension_indicators = [ind for ind, meta in indicators_catalog.items() 
                          if meta.get("dimension") == selected_dimension]
    
    if dimension_indicators:
        # Graphique temporel
        fig = make_subplots(rows=1, cols=1)
        
        for ind in dimension_indicators[:3]:  # Limite à 3 indicateurs pour la lisibilité
            if ind in data.columns:
                clean_data = data[["Année", ind]].dropna()
                if not clean_data.empty:
                    fig.add_trace(go.Scatter(
                        x=clean_data["Année"],
                        y=clean_data[ind],
                        mode='lines+markers',
                        name=ind
                    ))
        
        fig.update_layout(
            title=f"Évolution des indicateurs - {selected_dimension}",
            xaxis_title="Année",
            yaxis_title="Valeur"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison temporelle
    st.subheader("⏱️ Comparaison temporelle")
    col_year1, col_year2 = st.columns(2)
    
    with col_year1:
        year1 = st.selectbox("Année 1", data["Année"].dropna().astype(int), index=0)
    with col_year2:
        year2 = st.selectbox("Année 2", data["Année"].dropna().astype(int), index=min(5, len(data)-1))
    
    if year1 != year2:
        data_year1 = data[data["Année"] == year1].iloc[0] if not data[data["Année"] == year1].empty else pd.Series()
        data_year2 = data[data["Année"] == year2].iloc[0] if not data[data["Année"] == year2].empty else pd.Series()
        
        st.write(f"**Comparaison {year1} vs {year2}**")
        
        comparison_data = []
        for ind in ["PIB par habitant (USD)", "Population totale", "Accès à l'électricité (%)"]:
            if ind in data_year1 and ind in data_year2:
                val1 = data_year1[ind] if pd.notna(data_year1[ind]) else 0
                val2 = data_year2[ind] if pd.notna(data_year2[ind]) else 0
                evolution = ((val1 - val2) / val2 * 100) if val2 != 0 else 0
                comparison_data.append({
                    "Indicateur": ind,
                    f"{year2}": val2,
                    f"{year1}": val1,
                    "Évolution (%)": evolution
                })
        
        if comparison_data:
            st.dataframe(pd.DataFrame(comparison_data))

# ─────────────────────────────────────────────────────────────────────────────
# 5. ONGLET : CHATBOT INTELLIGENT
# ─────────────────────────────────────────────────────────────────────────────
def chatbot_tab():
    st.header("🤖 Assistant IA - Diagnostic Urbain")
    
    # Chargement des données pour le chatbot
    if 'chatbot_data' not in st.session_state:
        st.session_state.chatbot_data = None
    
    if st.button("🔄 Charger les données pour l'assistant"):
        with st.spinner("Chargement..."):
            st.session_state.chatbot_data = collect_all_indicators("MR")
        st.success("Données chargées pour l'assistant !")
    
    if st.session_state.chatbot_data is not None:
        data = st.session_state.chatbot_data
        latest_data = data.iloc[0] if not data.empty else pd.Series()
        
        st.info("💡 Posez vos questions sur les indicateurs de Nouakchott")
        
        # Interface de chat simple
        user_question = st.text_input("Votre question:", placeholder="Ex: Quel est le PIB par habitant en 2023?")
        
        if user_question:
            # Analyse simple de la question
            response = analyze_question(user_question, data, latest_data)
            st.write("🤖 **Assistant:**")
            st.write(response)
        
        # Questions prédéfinies
        st.subheader("❓ Questions fréquentes")
        
        col_q1, col_q2 = st.columns(2)
        
        with col_q1:
            if st.button("📊 Résumé des indicateurs clés"):
                summary = generate_summary(latest_data)
                st.write(summary)
        
        with col_q2:
            if st.button("📈 Analyse des tendances"):
                trends = analyze_trends(data)
                st.write(trends)
        
        # Recommandations automatiques
        st.subheader("💡 Recommandations")
        recommendations = generate_recommendations(latest_data)
        for rec in recommendations:
            st.info(rec)

def analyze_question(question, data, latest_data):
    """Analyse simple des questions utilisateur"""
    question_lower = question.lower()
    
    # Recherche d'indicateurs mentionnés
    for ind in indicators_catalog.keys():
        if any(word in question_lower for word in ind.lower().split()):
            value = latest_data.get(ind, None)
            if pd.notna(value):
                return f"L'indicateur '{ind}' pour la dernière année disponible est de {value:.2f}."
            else:
                return f"Désolé, aucune donnée disponible pour '{ind}'."
    
    # Questions générales
    if "résumé" in question_lower or "général" in question_lower:
        return generate_summary(latest_data)
    
    return "Je n'ai pas compris votre question. Essayez de mentionner un indicateur spécifique ou demandez un résumé général."

def generate_summary(latest_data):
    """Génère un résumé des indicateurs clés"""
    summary = "📊 **Résumé des indicateurs clés de Nouakchott:**\n\n"
    
    key_indicators = [
        "PIB par habitant (USD)",
        "Population totale", 
        "Accès à l'électricité (%)",
        "Accès à l'eau potable (%)",
        "Taux de chômage (%)"
    ]
    
    for ind in key_indicators:
        value = latest_data.get(ind, None)
        if pd.notna(value):
            summary += f"• **{ind}**: {value:.2f}\n"
        else:
            summary += f"• **{ind}**: Donnée non disponible\n"
    
    return summary

def analyze_trends(data):
    """Analyse les tendances sur 5 ans"""
    if len(data) < 5:
        return "Pas assez de données pour analyser les tendances."
    
    recent_data = data.head(5)
    trends = "📈 **Analyse des tendances (5 dernières années):**\n\n"
    
    key_indicators = ["PIB par habitant (USD)", "Population totale", "Accès à l'électricité (%)"]
    
    for ind in key_indicators:
        if ind in recent_data.columns:
            values = recent_data[ind].dropna()
            if len(values) >= 2:
                trend = "croissante" if values.iloc[0] > values.iloc[-1] else "décroissante"
                change = ((values.iloc[0] - values.iloc[-1]) / values.iloc[-1] * 100) if values.iloc[-1] != 0 else 0
                trends += f"• **{ind}**: Tendance {trend} ({change:+.1f}%)\n"
    
    return trends

def generate_recommendations(latest_data):
    """Génère des recommandations basées sur les données"""
    recommendations = []
    
    # Recommandations basées sur les seuils
    elec = latest_data.get("Accès à l'électricité (%)", 0)
    if pd.notna(elec) and elec < 80:
        recommendations.append("⚡ Priorité: Améliorer l'accès à l'électricité (actuellement sous 80%)")
    
    eau = latest_data.get("Accès à l'eau potable (%)", 0)
    if pd.notna(eau) and eau < 80:
        recommendations.append("💧 Priorité: Améliorer l'accès à l'eau potable (actuellement sous 80%)")
    
    chomage = latest_data.get("Taux de chômage (%)", 0)
    if pd.notna(chomage) and chomage > 15:
        recommendations.append("💼 Priorité: Réduire le taux de chômage (actuellement élevé)")
    
    if not recommendations:
        recommendations.append("✅ Les indicateurs principaux semblent dans des fourchettes acceptables")
    
    return recommendations

# ─────────────────────────────────────────────────────────────────────────────
# 6. ONGLET : AUTO-COLLECTOR
# ─────────────────────────────────────────────────────────────────────────────
def auto_collector_tab():
    st.header("🔍 Auto-Collector")
    st.info(f"📋 **{len(indicators_catalog)} indicateurs** dans le catalogue.")
    city = st.text_input("Entrez le nom de la ville", "Nouakchott")
    
    if st.button("🚀 Collecter tous les indicateurs"):
        with st.spinner("Collecte en cours…"):
            df = collect_all_indicators("MR")
        st.success(f"✅ {len(df.columns)-1} indicateurs récupérés (NaN si indisponible).")
        st.dataframe(df)
        
        st.download_button("📥 Télécharger CSV",
                           data=df.to_csv(index=False),
                           file_name=f"indicateurs_{city}_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

    if st.button("📚 Afficher le catalogue complet"):
        for src in sorted(set(m['source'] for m in indicators_catalog.values())):
            with st.expander(f"{src}"):
                for ind, meta in indicators_catalog.items():
                    if meta["source"] == src:
                        st.markdown(f"• **{ind}** — `{meta['code']}`")

# ─────────────────────────────────────────────────────────────────────────────
# 7. FONCTION PRINCIPALE STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    create_header()
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🏙️ Diagnostic", "📊 Dashboard", "🤖 Chatbot", "🔍 Auto-Collector"]
    )
    with tab1: diagnostic_tab()
    with tab2: dashboard_tab()
    with tab3: chatbot_tab()
    with tab4: auto_collector_tab()

if __name__ == "__main__":
    main()
