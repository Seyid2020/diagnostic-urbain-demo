###############################################################################
# ░█▀▀▀ ░█▀▀▀ ░█▄─░█ ░█▀▀█ 　 Diagnostic Urbain Intelligent
# ░█▀▀▀ ░█▀▀▀ ░█░█░█ ░█─── 　 Plateforme Streamlit – Collecte Auto d’indicateurs
# ░█▄▄▄ ░█▄▄▄ ░█──▀█ ░█▄▄█ 　 (rempli NaN si un indicateur est introuvable)
###############################################################################
import os
os.environ["STREAMLIT_THREADING_MODE"] = "single"   # ← important avec wbdata

import streamlit as st
import pandas as pd
import wbdata
from functools import reduce
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 1. CATALOGUE DES INDICATEURS (34 pour l’exemple, extensible à 65)
# ─────────────────────────────────────────────────────────────────────────────
indicators_catalog = {
    # SOCIÉTÉ
    "Population totale":                 {"code": "SP.POP.TOTL",        "source": "Banque mondiale"},
    "Taux de croissance démographique (%)": {"code": "SP.POP.GROW",    "source": "Banque mondiale"},
    "Densité de population (hab/km²)":   {"code": "EN.POP.DNST",        "source": "Banque mondiale"},
    "Taux d'alphabétisation des adultes (%)": {"code": "SE.ADT.LITR.ZS","source": "Banque mondiale"},
    "Espérance de vie à la naissance":   {"code": "SP.DYN.LE00.IN",     "source": "Banque mondiale"},
    "Taux de mortalité infantile (‰)":   {"code": "SP.DYN.IMRT.IN",     "source": "Banque mondiale"},
    "Indice de développement humain":    {"code": "UNDP.HDI",           "source": "PNUD"},           # pas WB
    "Taux de pauvreté (%)":              {"code": "SI.POV.NAHC",        "source": "Banque mondiale"},# code poss. absent
    "Coefficient de Gini":              {"code": "SI.POV.GINI",        "source": "Banque mondiale"},
    "Accès à l'éducation primaire (%)":  {"code": "SE.PRM.NENR",        "source": "Banque mondiale"},
    # HABITAT
    "Population urbaine (%)":            {"code": "SP.URB.TOTL.IN.ZS",  "source": "Banque mondiale"},
    "Croissance urbaine annuelle (%)":   {"code": "SP.URB.GROW",        "source": "Banque mondiale"},
    "Accès à l'eau potable (%)":         {"code": "SH.H2O.BASW.ZS",     "source": "Banque mondiale"},
    "Accès à l'assainissement (%)":      {"code": "SH.STA.BASS.ZS",     "source": "Banque mondiale"},
    "Accès à l'électricité (%)":         {"code": "EG.ELC.ACCS.ZS",     "source": "Banque mondiale"},
    # DÉVELOPPEMENT SPATIAL
    "Superficie urbaine (km²)":          {"code": "AG.LND.TOTL.UR.K2",  "source": "Banque mondiale"},# code poss. absent
    "Zones vertes urbaines (%)":         {"code": "AG.LND.FRST.ZS",     "source": "Banque mondiale"},
    # INFRASTRUCTURES
    "Routes pavées (%)":                 {"code": "IS.ROD.PAVE.ZS",     "source": "Banque mondiale"},
    "Utilisateurs d'Internet (%)":       {"code": "IT.NET.USER.ZS",     "source": "Banque mondiale"},
    "Abonnements téléphonie mobile":     {"code": "IT.CEL.SETS.P2",     "source": "Banque mondiale"},
    # ENVIRONNEMENT
    "Émissions CO2 (t/hab)":             {"code": "EN.ATM.CO2E.PC",     "source": "Banque mondiale"},
    "Consommation d'énergie (kg éq. pétrol/hab)": {"code":"EG.USE.PCAP.KG.OE","source":"Banque mondiale"},
    "Énergies renouvelables (% conso. totale)":   {"code":"EG.FEC.RNEW.ZS","source":"Banque mondiale"},
    # GOUVERNANCE (codes WB-GGI ; s’ils échouent, NaN)
    "Indice de gouvernance (Voix & Redevabilité)": {"code":"VA.EST","source":"Banque mondiale"},
    "Efficacité gouvernementale":        {"code": "GE.EST",             "source": "Banque mondiale"},
    "État de droit":                     {"code": "RL.EST",             "source": "Banque mondiale"},
    # ÉCONOMIE
    "PIB par habitant (USD)":            {"code": "NY.GDP.PCAP.CD",     "source": "Banque mondiale"},
    "Taux de chômage (%)":               {"code": "SL.UEM.TOTL.ZS",     "source": "Banque mondiale"},
    "Taux d'inflation (%)":              {"code": "FP.CPI.TOTL.ZG",     "source": "Banque mondiale"},
    "Formation brute de capital fixe (% PIB)": {"code":"NE.GDI.FTOT.ZS","source":"Banque mondiale"},
    "Commerce (% PIB)":                  {"code": "NE.TRD.GNFS.ZS",     "source": "Banque mondiale"},
    "IDE net entrant (% PIB)":           {"code": "BX.KLT.DINV.WD.GD.ZS","source":"Banque mondiale"},
    "Dépenses publiques éducation (% PIB)": {"code":"SE.XPD.TOTL.GD.ZS","source":"Banque mondiale"},
    "Dépenses publiques santé (% PIB)":  {"code": "SH.XPD.GHED.GD.ZS",  "source": "Banque mondiale"}
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────
def create_header():
    st.title("Diagnostic Urbain Intelligent - Ville de Nouakchott")
    st.markdown("Bienvenue dans la plateforme de diagnostic urbain intelligent.")

# ---------- Collecte robuste (NaN si échec) ----------
def collect_all_indicators(country_code="MR"):
    """
    Tente de récupérer chaque indicateur individuellement.
    Si un code échoue → colonne remplie de NaN.
    Retourne un DataFrame fusionné, indexé par Année (descendant).
    """
    # Base d’années 1960 → année courante (desc)
    current_year = datetime.now().year
    base_df = pd.DataFrame({"Année": list(range(current_year, 1959, -1))})
    dfs = []   # DataFrames individuels
    
    for ind_name, meta in indicators_catalog.items():
        if meta["source"] != "Banque mondiale":
            # Source non WB : on crée colonne NaN directement
            tmp = base_df.copy()
            tmp[ind_name] = pd.NA
            dfs.append(tmp)
            continue
        
        code = meta["code"]
        try:
            # wbdata renvoie (index=date, series=valeur)
            df = wbdata.get_dataframe({code: ind_name},
                                      country=country_code)
            df = df.reset_index().rename(columns={"date": "Année"})
            dfs.append(df)
        except Exception:
            # En cas d’erreur (code inexistant, etc.) → colonne NaN
            tmp = base_df.copy()
            tmp[ind_name] = pd.NA
            dfs.append(tmp)
    
    # Fusionner toutes les colonnes sur 'Année'
    df_final = reduce(lambda left, right: pd.merge(left, right, on="Année", how="outer"), dfs)
    df_final.sort_values("Année", ascending=False, inplace=True)
    return df_final

# ─────────────────────────────────────────────────────────────────────────────
# 3. ONGLET : DIAGNOSTIC
# ─────────────────────────────────────────────────────────────────────────────
def diagnostic_tab():
    st.header("🏙️ Diagnostic Urbain")
    st.write("Ici, vous pouvez saisir et analyser les données urbaines.")
    if st.button("📥 Importer les données collectées automatiquement"):
        data = collect_all_indicators("MR")
        st.success("Données importées dans le diagnostic !")
        st.dataframe(data.tail())

# ─────────────────────────────────────────────────────────────────────────────
# 4. ONGLET : DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def dashboard_tab():
    st.header("📊 Dashboard")
    if st.button("📊 Générer dashboard automatique"):
        with st.spinner("Génération du dashboard…"):
            data = collect_all_indicators("MR")
            st.success("Dashboard généré !")
            if "PIB par habitant (USD)" in data.columns:
                st.line_chart(data[["Année", "PIB par habitant (USD)"]].set_index("Année").dropna())
            if "Population totale" in data.columns:
                st.line_chart(data[["Année", "Population totale"]].set_index("Année").dropna())
            st.write("Données les plus récentes :")
            st.dataframe(data.head(1))

# ─────────────────────────────────────────────────────────────────────────────
# 5. ONGLET : CHATBOT (placeholder)
# ─────────────────────────────────────────────────────────────────────────────
def chatbot_tab():
    st.header("🤖 Chatbot")
    st.write("Posez vos questions sur le diagnostic urbain (fonctionnalité à venir).")

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
        # Téléchargement
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
