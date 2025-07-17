import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="UrbanAI Diagnostic", 
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour améliorer le design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e8b57);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f4e79;
    }
    .chat-message {
        background: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .diagnostic-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal avec logo
st.markdown("""
<div class="main-header">
    <h1>🏙️ UrbanAI Diagnostic</h1>
    <p>La plateforme intelligente pour le diagnostic urbain en Afrique</p>
    <p><em>Générez, explorez, et comprenez votre ville avec l'IA</em></p>
</div>
""", unsafe_allow_html=True)

# Initialisation des données de session
if "diagnostics" not in st.session_state:
    st.session_state["diagnostics"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Fonction pour générer le diagnostic avec Hugging Face (gratuit)
def generate_diagnostic_hf(ville, population, defis, priorites, commentaire):
    """Génère un diagnostic urbain avec l'API Hugging Face (gratuite)"""
    
    prompt = f"""Génère un diagnostic urbain détaillé pour la ville de {ville}.
Population: {population:,} habitants.
Défis: {', '.join(defis) if defis else 'aucun défi spécifique'}.
Priorités: {', '.join(priorites) if priorites else 'aucune priorité spécifique'}.
Commentaire: {commentaire if commentaire else 'aucun'}.

Structure le diagnostic avec:
1. Résumé exécutif
2. Contexte démographique
3. Analyse des défis
4. Recommandations
5. Conclusion"""

    try:
        # API Hugging Face (modèle gratuit)
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": "Bearer hf_xxxxxxxxxx"}  # Tu peux laisser ça pour le prototype
        
        # Pour le prototype, on simule une réponse IA réaliste
        diagnostic_simule = f"""
## 📋 Résumé Exécutif
La ville de {ville}, avec ses {population:,} habitants, présente un profil urbain typique des métropoles africaines en croissance rapide.

## 👥 Contexte Démographique
Avec une population de {population:,} habitants, {ville} fait face à une urbanisation accélérée qui nécessite une planification adaptée.

## ⚠️ Analyse des Défis Identifiés
Les principaux défis identifiés sont :
{chr(10).join([f"• **{defi}** : Nécessite une attention prioritaire" for defi in defis]) if defis else "• Aucun défi spécifique identifié"}

## 🎯 Recommandations Stratégiques
Basées sur les priorités définies :
{chr(10).join([f"• Développer des initiatives de **{priorite.lower()}**" for priorite in priorites]) if priorites else "• Évaluation générale recommandée"}

## 📊 Conclusion
{ville} dispose d'un potentiel de développement important. Une approche intégrée, basée sur les données et les besoins locaux, est recommandée pour optimiser la gestion urbaine et améliorer la qualité de vie des habitants.

*Diagnostic généré par UrbanAI - {datetime.now().strftime("%d/%m/%Y à %H:%M")}*
        """
        
        return diagnostic_simule
        
    except Exception as e:
        return f"Erreur lors de la génération : {e}"

# Fonction chatbot simulé
def chatbot_response(question):
    """Chatbot simulé pour l'assistance"""
    responses = {
        "comment": "Pour générer un diagnostic, va dans l'onglet 'Nouveau Diagnostic' et remplis le formulaire avec les informations de ta ville.",
        "diagnostic": "Un diagnostic urbain analyse les défis et opportunités d'une ville pour proposer des recommandations d'amélioration.",
        "données": "Tu peux saisir le nom de ta ville, sa population, les défis principaux et tes priorités de développement.",
        "export": "Dans le dashboard, tu peux voir tous tes diagnostics générés. L'export PDF sera disponible prochainement.",
        "aide": "Je peux t'aider avec la génération de diagnostics, l'utilisation de la plateforme, ou répondre à tes questions sur l'urbanisme."
    }
    
    question_lower = question.lower()
    for key, response in responses.items():
        if key in question_lower:
            return f"🤖 {response}"
    
    return "🤖 Je suis là pour t'aider ! Pose-moi des questions sur la génération de diagnostics, l'utilisation de la plateforme, ou l'urbanisme en général."

# Création des onglets
tab1, tab2, tab3 = st.tabs(["🆕 Nouveau Diagnostic", "📊 Dashboard", "💬 Chatbot"])

# ONGLET 1: NOUVEAU DIAGNOSTIC
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📝 Informations sur votre ville")
        
        with st.form("diagnostic_form"):
            ville = st.text_input("🏙️ Nom de la ville", "Nouakchott")
            population = st.number_input("👥 Population estimée", min_value=1000, value=1000000, step=10000)
            
            defis = st.multiselect(
                "⚠️ Principaux défis urbains",
                ["💧 Eau", "⚡ Énergie", "🏠 Logement", "🚌 Transport", "🌍 Environnement", "🏥 Santé", "🎓 Éducation"],
                default=["💧 Eau", "🏠 Logement"]
            )
            
            priorites = st.multiselect(
                "🎯 Priorités de développement",
                ["🤖 Smart City", "🌱 Durabilité", "🤝 Inclusion sociale", "📈 Croissance économique"],
                default=["🌱 Durabilité"]
            )
            
            commentaire = st.text_area("💬 Commentaire libre", placeholder="Ajoutez des informations spécifiques sur votre ville...")
            
            submit = st.form_submit_button("🚀 Générer le diagnostic", use_container_width=True)
    
    with col2:
        if submit:
            st.success(f"✅ Diagnostic en cours de génération pour {ville}...")
            
            with st.spinner("🤖 L'IA analyse votre ville..."):
                diagnostic_ia = generate_diagnostic_hf(ville, population, defis, priorites, commentaire)
            
            # Stockage du diagnostic
            nouveau_diagnostic = {
                "id": len(st.session_state["diagnostics"]) + 1,
                "ville": ville,
                "population": population,
                "defis": defis,
                "priorites": priorites,
                "commentaire": commentaire,
                "diagnostic": diagnostic_ia,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            st.session_state["diagnostics"].append(nouveau_diagnostic)
            
            st.success(f"✅ Diagnostic généré pour {ville} !")
            
            # Affichage du résumé
            st.markdown("### 📊 Résumé des données")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🏙️ Ville</h4>
                    <p>{ville}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>👥 Population</h4>
                    <p>{population:,}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_c:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>⚠️ Défis</h4>
                    <p>{len(defis)} identifiés</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Affichage du diagnostic
            st.markdown("### 🤖 Diagnostic IA")
            st.markdown(f"""
            <div class="diagnostic-card">
                {diagnostic_ia}
            </div>
            """, unsafe_allow_html=True)
            
            # Graphique des défis
            if defis:
                st.markdown("### 📈 Analyse visuelle des défis")
                fig, ax = plt.subplots(figsize=(10, 6))
                defis_clean = [d.split(' ', 1)[1] if ' ' in d else d for d in defis]
                scores = np.random.randint(3, 10, len(defis))
                
                bars = ax.bar(defis_clean, scores, color=['#1f4e79', '#2e8b57', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
                ax.set_title(f"Niveau d'urgence des défis - {ville}", fontsize=16, fontweight='bold')
                ax.set_ylabel("Score d'urgence (1-10)", fontsize=12)
                ax.set_ylim(0, 10)
                
                # Ajouter les valeurs sur les barres
                for bar, score in zip(bars, scores):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           str(score), ha='center', va='bottom', fontweight='bold')
                
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
        
        else:
            st.info("👈 Remplis le formulaire pour générer un diagnostic personnalisé")
            st.markdown("""
            ### 🎯 Comment ça marche ?
            
            1. **📝 Remplis le formulaire** avec les informations de ta ville
            2. **🚀 Clique sur "Générer"** pour lancer l'analyse IA
            3. **📊 Consulte le diagnostic** détaillé et les recommandations
            4. **💾 Retrouve tous tes diagnostics** dans le Dashboard
            """)

# ONGLET 2: DASHBOARD
with tab2:
    st.markdown("### 📊 Dashboard des diagnostics générés")
    
    if st.session_state["diagnostics"]:
        # Métriques générales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏙️ Villes analysées", len(st.session_state["diagnostics"]))
        
        with col2:
            total_pop = sum([d["population"] for d in st.session_state["diagnostics"]])
            st.metric("👥 Population totale", f"{total_pop:,}")
        
        with col3:
            all_defis = []
            for d in st.session_state["diagnostics"]:
                all_defis.extend(d["defis"])
            st.metric("⚠️ Défis identifiés", len(set(all_defis)))
        
        with col4:
            st.metric("📅 Dernier diagnostic", st.session_state["diagnostics"][-1]["date"])
        
        st.markdown("---")
        
        # Liste des diagnostics
        for i, diagnostic in enumerate(reversed(st.session_state["diagnostics"])):
            with st.expander(f"🏙️ {diagnostic['ville']} - {diagnostic['date']}", expanded=(i==0)):
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.write(f"**👥 Population :** {diagnostic['population']:,}")
                    st.write(f"**⚠️ Défis :** {', '.join([d.split(' ', 1)[1] if ' ' in d else d for d in diagnostic['defis']])}")
                    st.write(f"**🎯 Priorités :** {', '.join([p.split(' ', 1)[1] if ' ' in p else p for p in diagnostic['priorites']])}")
                    if diagnostic['commentaire']:
                        st.write(f"**💬 Commentaire :** {diagnostic['commentaire']}")
                
                with col_right:
                    st.markdown(diagnostic["diagnostic"])
                
                # Boutons d'action
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button(f"📄 Exporter PDF", key=f"pdf_{diagnostic['id']}"):
                        st.info("Export PDF - Fonctionnalité à venir !")
                with col_btn2:
                    if st.button(f"📊 Voir graphiques", key=f"graph_{diagnostic['id']}"):
                        st.info("Graphiques détaillés - Fonctionnalité à venir !")
                with col_btn3:
                    if st.button(f"🗑️ Supprimer", key=f"delete_{diagnostic['id']}"):
                        st.warning("Suppression - Fonctionnalité à venir !")
    
    else:
        st.info("📭 Aucun diagnostic généré pour l'instant. Va dans l'onglet 'Nouveau Diagnostic' pour commencer !")
        
        # Graphique de démonstration
        st.markdown("### 📈 Exemple de visualisation")
        fig, ax = plt.subplots(figsize=(10, 6))
        villes_demo = ["Nouakchott", "Dakar", "Bamako", "Ouagadougou", "Niamey"]
        populations_demo = [1000000, 3500000, 2500000, 2200000, 1300000]
        
        ax.bar(villes_demo, populations_demo, color=['#1f4e79', '#2e8b57', '#ff6b6b', '#4ecdc4', '#45b7d1'])
        ax.set_title("Exemple : Population des capitales ouest-africaines", fontsize=16, fontweight='bold')
        ax.set_ylabel("Population", fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

# ONGLET 3: CHATBOT
with tab3:
    st.markdown("### 💬 Assistant IA - Pose tes questions")
    
    # Affichage de l'historique du chat
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            st.markdown(f"""
            <div style="text-align: right; margin: 1rem 0;">
                <div style="background: #1f4e79; color: white; padding: 1rem; border-radius: 10px; display: inline-block; max-width: 70%;">
                    👤 {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message">
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Zone de saisie
    col_input, col_send = st.columns([4, 1])
    
    with col_input:
        user_question = st.text_input("Tape ta question ici...", key="chat_input", placeholder="Ex: Comment générer un diagnostic ?")
    
    with col_send:
        if st.button("📤 Envoyer", use_container_width=True) and user_question:
            # Ajouter la question de l'utilisateur
            st.session_state["chat_history"].append({"role": "user", "content": user_question})
            
            # Générer et ajouter la réponse
            response = chatbot_response(user_question)
            st.session_state["chat_history"].append({"role": "assistant", "content": response})
            
            # Rerun pour afficher la conversation
            st.rerun()
    
    # Questions suggérées
    st.markdown("### 💡 Questions suggérées")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❓ Comment générer un diagnostic ?"):
            st.session_state["chat_history"].append({"role": "user", "content": "Comment générer un diagnostic ?"})
            st.session_state["chat_history"].append({"role": "assistant", "content": chatbot_response("comment")})
            st.rerun()
        
        if st.button("📊 Qu'est-ce qu'un diagnostic urbain ?"):
            st.session_state["chat_history"].append({"role": "user", "content": "Qu'est-ce qu'un diagnostic urbain ?"})
            st.session_state["chat_history"].append({"role": "assistant", "content": chatbot_response("diagnostic")})
            st.rerun()
    
    with col2:
        if st.button("💾 Comment exporter mes résultats ?"):
            st.session_state["chat_history"].append({"role": "user", "content": "Comment exporter mes résultats ?"})
            st.session_state["chat_history"].append({"role": "assistant", "content": chatbot_response("export")})
            st.rerun()
        
        if st.button("🆘 J'ai besoin d'aide"):
            st.session_state["chat_history"].append({"role": "user", "content": "J'ai besoin d'aide"})
            st.session_state["chat_history"].append({"role": "assistant", "content": chatbot_response("aide")})
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🏙️ <strong>UrbanAI Diagnostic</strong> - Développé par Dr. Seyid Ebnou</p>
    <p>Plateforme intelligente pour le diagnostic urbain en Afrique</p>
</div>
""", unsafe_allow_html=True)
