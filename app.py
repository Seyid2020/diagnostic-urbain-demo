st.markdown("""
### 📝 Remplir le formulaire détaillé
[👉 Cliquez ici pour accéder au formulaire Microsoft Forms]
(https://forms.office.com/Pages/ResponsePage.aspx?id=V2FiOUegiUaHom-mRctct4nQ0_9pFOVOtOpqm9QvhpxUNDlWTVk1UjI4VldPS0xWUk1EVUZaMEs4Ty4u)
""")

st.info("""
**Étapes à suivre :**
1. Cliquez sur le lien ci-dessus pour remplir le formulaire détaillé sur votre ville.
2. Une fois le formulaire soumis, vos réponses seront traitées par notre équipe/plateforme.
3. Vous recevrez un diagnostic personnalisé basé sur vos réponses, enrichi par l’IA et les données récentes.
""")
if st.button("✅ J'ai soumis le formulaire, continuer la génération du diagnostic"):
    st.write("Merci ! Veuillez saisir ici les informations principales de votre formulaire pour générer un diagnostic de démonstration.")
    ville = st.text_input("Nom de la ville", "Nouakchott")
    population = st.number_input("Population", min_value=1000, value=1000000)
    defis = st.multiselect("Défis principaux", ["Eau", "Énergie", "Logement", "Transport", "Environnement", "Santé", "Éducation"])
    commentaire = st.text_area("Commentaire libre")
    if st.button("Générer le diagnostic"):
        # Simule l'enrichissement et la génération IA
        infos_web = "Selon le rapport de l'UN-Habitat 2023, Nouakchott fait face à une urbanisation rapide et des défis majeurs en matière d'accès à l'eau."
        donnees_internes = "Taux d'accès à l'eau potable : 65%. Nombre de forages : 15. Qualité de l'eau : Moyenne."
        diagnostic = f'''
        ## Résumé
        {ville} compte {population:,} habitants. Les défis principaux sont : {', '.join(defis)}.
        {infos_web}
        
        ## Analyse
        {donnees_internes}
        {commentaire}
        
        ## Recommandations
        - Renforcer l'accès à l'eau potable.
        - Améliorer la gestion des ressources énergétiques.
        - Développer des infrastructures de transport durable.
        '''
        st.success("Diagnostic généré ! (démo)")
        st.markdown(diagnostic)
        st.button("Exporter en PDF (bientôt disponible)")
