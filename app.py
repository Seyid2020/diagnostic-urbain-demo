import streamlit as st

st.set_page_config(page_title="Diagnostic Urbain", layout="wide")

# Barre latérale pour la navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Accueil", "Formulaire Diagnostic", "Chatbot", "Dashboard"]
)

if page == "Accueil":
    st.markdown("# Diagnostic Urbain")
    st.write("Bienvenue sur la plateforme de diagnostic urbain.")

elif page == "Formulaire Diagnostic":
    st.markdown("## 📝 Remplir le formulaire détaillé")
    st.markdown(
        "[👉 Cliquez ici pour accéder au formulaire Microsoft Forms](https://forms.office.com/Pages/ResponsePage.aspx?id=V2FiOUegiUaHom-mRctct4nQ0_9pFOVOtOpqm9QvhpxUNDlWTVk1UjI4VldPS0xWUk1EVUZaMEs4Ty4u)"
    )
    st.write("""
    **Étapes à suivre :**
    1. Cliquez sur le lien ci-dessus pour remplir le formulaire détaillé sur votre ville.
    2. Une fois le formulaire soumis, vos réponses seront traitées par notre équipe/plateforme.
    3. Vous recevrez un diagnostic personnalisé basé sur vos réponses, enrichi par l’IA et les données récentes.
    """)
    st.write("Merci ! Veuillez saisir ici les informations principales de votre formulaire pour générer un diagnostic de démonstration.")

    ville = st.text_input("Nom de la ville", "Nouakchott")
    population = st.number_input("Population", min_value=0, value=1000000)
    defis = st.text_area("Défis principaux")
    commentaire = st.text_area("Commentaire libre")

    if st.button("Générer le diagnostic"):
        st.success(f"Diagnostic généré pour {ville} (Population : {population})")
        # Ici tu ajoutes l'appel à l'IA ou à ton diagnostic

elif page == "Chatbot":
    st.markdown("## 🤖 Chatbot")
    st.write("Posez vos questions sur le diagnostic urbain ici.")
    # Ajoute ici ton code chatbot

elif page == "Dashboard":
    st.markdown("## 📊 Dashboard")
    st.write("Visualisez les données urbaines ici.")
    # Ajoute ici ton code dashboard
