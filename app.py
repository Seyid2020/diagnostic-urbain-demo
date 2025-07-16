import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

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

# Affichage des résultats
if submit:
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
        st.write("### 🤖 Diagnostic IA (exemple simulé)")
        diagnostic_text = f"""
        **Analyse urbaine pour {ville}**
        
        Avec une population de {population:,} habitants, {ville} présente des caractéristiques urbaines spécifiques qui nécessitent une approche adaptée.
        
        **Défis identifiés :**
        {chr(10).join([f"• {defi}" for defi in defis]) if defis else "• Aucun défi spécifique identifié"}
        
        **Recommandations prioritaires :**
        {chr(10).join([f"• Développer des solutions pour {priorite.lower()}" for priorite in priorites]) if priorites else "• Évaluation générale recommandée"}
        
        **Conclusion :**
        Une approche intégrée, basée sur les données et les besoins locaux, est recommandée pour optimiser la gestion urbaine de {ville}.
        """
        st.write(diagnostic_text)
        
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
