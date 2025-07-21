with tab1:
    st.markdown("""
    <div style="background:#eafaf1; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <b>📝 Lancez un diagnostic personnalisé de votre ville en quelques clics !</b><br>
        Saisissez vos données, l’IA s’occupe du reste.
    </div>
    """, unsafe_allow_html=True)

    # Ajout du lien vers le formulaire externe + instructions
    st.markdown("""
    <div style="background:#fff3cd; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <b>📝 Vous pouvez aussi remplir le <a href="https://forms.office.com/Pages/ResponsePage.aspx?id=V2FiOUegiUaHom-mRctct4nQ0_9pFOVOtOpqm9QvhpxUNDlWTVk1UjI4VldPS0xWUk1EVUZaMEs4Ty4u" target="_blank">formulaire détaillé en ligne</a>.</b><br>
        Après soumission, copiez les informations principales ici pour générer un diagnostic instantané avec l’IA.
    </div>
    """, unsafe_allow_html=True)

    # Choix du moteur IA
    moteur_ia = st.selectbox("Choisissez le moteur IA", ["OpenAI", "Hugging Face"])

    with st.form("diagnostic_form"):
        ville = st.text_input("🏙️ Nom de la ville", "Nouakchott")
        population = st.number_input("👥 Population estimée", min_value=1000, value=1000000, step=10000)
        defis = st.multiselect(
            "⚠️ Principaux défis urbains",
            ["Eau", "Énergie", "Logement", "Transport", "Environnement", "Santé", "Éducation"],
            default=["Eau", "Logement"]
        )
        priorites = st.multiselect(
            "🎯 Priorités de développement",
            ["Smart City", "Durabilité", "Inclusion sociale", "Croissance économique"],
            default=["Durabilité"]
        )
        commentaire = st.text_area("💬 Commentaire libre", placeholder="Ajoutez des informations spécifiques sur votre ville...")
        submit = st.form_submit_button("🚀 Générer le diagnostic")

    if submit:
        st.success(f"✅ Diagnostic en cours de génération pour {ville}...")

        prompt = f"""
Génère un rapport urbain structuré pour la ville de {ville} ({population:,} habitants).
Défis principaux : {', '.join(defis) if defis else 'aucun'}.
Priorités : {', '.join(priorites) if priorites else 'aucune'}.
Commentaire : {commentaire if commentaire else 'aucun'}.

Structure du rapport :
1. Résumé exécutif
2. Contexte démographique
3. Analyse des défis
4. Recommandations
5. Conclusion
        """

        rapport = ""
        if moteur_ia == "OpenAI":
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7,
                )
                rapport = response.choices[0].message.content
            except Exception as e:
                rapport = f"Erreur lors de la génération du rapport : {e}"

        elif moteur_ia == "Hugging Face":
            # Simulation Hugging Face (remplace par ton vrai appel API si tu veux)
            rapport = f"""
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

        st.markdown("### 🤖 Rapport IA")
        st.markdown(f"""
        <div class="diagnostic-card" style="background:white; padding:1.5rem; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); margin:1rem 0;">
            {rapport}
        </div>
        """, unsafe_allow_html=True)
