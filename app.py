import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import openai # Importe la librairie OpenAI

# Configure la clé API OpenAI
# Streamlit va chercher la clé dans les secrets que tu as configurés
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Diagnostic Urbain IA", layout="wide")

st.title("🏙️ Diagnostic Urbain IA - Prototype")
st.markdown("---")

# Sidebar pour le formulaire
st.sidebar.header("📝 Remplis le formulaire pour ta ville")

# Formulaire utilisateur
with st.sidebar.form("diagnostic_form"):
    ville = st.text_input("Nom de la ville", "Nouakchott")
    population = st.number_input("Population estimée", min_value=1000, value=1000000)
    defis = st.multiselect(
        "Principaux défis urbains",
        ["Eau", "Énergie", "Logement", "Transport", "Environnement", "Santé", "Éducation"]
    )
    priorites = st.multiselect(
        "Priorités de développement",
        ["Smart City", "Durabilité", "Inclusion sociale", "Croissance économique"]
    )
    commentaire = st.text_area("Commentaire libre")
    submit = st.form_submit_button("🚀 Générer le diagnostic")

# Fonction pour générer le diagnostic avec OpenAI
def generate_diagnostic(ville, population, defis, priorites, commentaire):
    prompt = f"""
    Génère un diagnostic urbain détaillé (environ 300-500 mots) pour la ville de {ville}.
    La population estimée est de {population:,} habitants.

    Les principaux défis identifiés sont : {', '.join(defis) if defis else 'aucun défi spécifique mentionné'}.
    Les priorités de développement sont : {', '.join(priorites) if priorites else 'aucune priorité spécifique mentionnée'}.
    Commentaire additionnel : {commentaire if commentaire else 'aucun.'}

    Le diagnostic doit être structuré avec des titres et des paragraphes, similaire aux rapports de la Banque Mondiale ou de l'UN-Habitat.
    Il doit inclure :
    1. Un résumé exécutif.
    2. Une section sur le contexte et la démographie.
    3. Une analyse des défis mentionnés.
    4. Des recommandations basées sur les priorités.
    5. Une conclusion.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini", # Ou "gpt-4o" si tu as plus de crédit et veux une meilleure qualité
            messages=[
                {"role": "system", "content": "Tu es un expert en développement urbain et en data science, spécialisé dans les diagnostics de villes africaines."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000, # Augmente si tu veux des diagnostics plus longs
            temperature=0.7 # Contrôle la créativité (0.2 pour plus factuel, 1.0 pour plus créatif)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur lors de la génération du diagnostic : {e}"

# Affichage des résultats
if submit:
    st.success(f"✅ Diagnostic en cours de génération pour {ville}...")
    
    # Affiche un spinner pendant la génération
    with st.spinner("L'IA est en train de rédiger le diagnostic..."):
        diagnostic_ia = generate_diagnostic(ville, population, defis, priorites, commentaire)
    
    st.success(f"✅ Diagnostic généré pour {ville} !")
    
    # Colonnes pour un meilleur affichage
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Résumé des données")
        st.write(f"**🏙️ Ville :** {ville}")
        st.write(f"**👥 Population :** {population:,}")
        st.write(f"**⚠️ Défis principaux :** {', '.join(defis) if defis else 'Aucun sélectionné'}")
        st.write(f"**🎯 Priorités :** {', '.join(priorites) if priorites else 'Aucune sélectionnée'}")
        if commentaire:
            st.write(f"**💬 Commentaire :** {commentaire}")
    
    with col2:
        st.write("### 🤖 Diagnostic IA")
        st.markdown(diagnostic_ia) # Utilise st.markdown pour afficher le texte formaté par l'IA
        
        # Graphique simple (exemple)
        if defis:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(defis, np.random.randint(1, 10, len(defis)))
            ax.set_title(f"Niveau d'urgence des défis - {ville}")
            ax.set_ylabel("Score d'urgence")
            plt.xticks(rotation=45)
            st.pyplot(fig)

else:
    st.info("👈 Remplis le formulaire dans la barre latérale pour générer un diagnostic")
    
    # Page d'accueil
    st.write("### 🎯 À propos de cette plateforme")
    st.write("""
    Cette plateforme utilise l'intelligence artificielle pour générer des diagnostics urbains complets et personnalisés.
    
    **Fonctionnalités :**
    - 📝 Formulaire interactif pour saisir les données de votre ville
    - 🤖 Génération automatique de diagnostic urbain
    - 📊 Visualisations et analyses graphiques
    - 💡 Recommandations personnalisées
    """)
