import streamlit as st
import openai
from datetime import datetime
import pandas as pd
from io import BytesIO
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import markdown
import requests

# --- Fonction Hugging Face ---
def generate_groq_report(prompt, groq_api_key):
    """Utilise l'API Groq (gratuite)"""
    import requests
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "llama3-8b-8192",
        "max_tokens": 1500,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Erreur Groq: {response.text}"


# Dans votre interface, ajoutez cette option :
moteur_ia = st.selectbox("Choisissez le moteur IA", ["OpenAI", "Hugging Face", "Ollama (Local)"])

# Dans la génération du rapport :
elif moteur_ia == "Ollama (Local)":
    with st.spinner("Génération IA Ollama en cours..."):
        rapport = generate_ollama_report(prompt)

# --- PAGE D'ACCUEIL & PHRASES D'ACCROCHE ---
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    padding: 2rem 2rem 1rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 16px rgba(44, 62, 80, 0.08);
    text-align: center;
}
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 1.5rem;
}
</style>
<div class="logo-container">
    <img src="https://cdn.abacus.ai/images/d1788567-27c2-4731-b4f0-26dc07fcd4f3.png" alt="CUS Logo" width="320">
</div>
<div class="main-header">
    <h1 style="color:#1f4e79;">🏙️ UrbanAI Diagnostic</h1>
    <h3 style="color:#e67e22;">La plateforme intelligente pour le diagnostic urbain en Afrique</h3>
    <p style="font-size:1.1rem; color:#34495e;">
        <b>Description :</b> Diagnostic rapide, interactif et enrichi par l’IA, basé sur vos réponses et vos documents. Générez un rapport complet, structuré et personnalisé pour votre ville.
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🆕 Nouveau Diagnostic", "📊 Dashboard", "💬 Chatbot"])

def markdown_to_pdf(text):
    # Convertit le markdown en texte brut (simple)
    plain_text = markdown.markdown(text)
    # Supprime les balises HTML pour le PDF (option simple)
    import re
    plain_text = re.sub('<[^<]+?>', '', plain_text)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    lines = simpleSplit(plain_text, 'Helvetica', 12, width - 2*margin)
    for line in lines:
        if y < margin:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line)
        y -= 15
    c.save()
    buffer.seek(0)
    return buffer

with tab1:
    st.markdown("""
    <div style="background:#eafaf1; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <b>📝 Remplissez chaque section, ajoutez vos documents, et obtenez un diagnostic urbain complet et personnalisé !</b>
    </div>
    """, unsafe_allow_html=True)

    moteur_ia = st.selectbox("Choisissez le moteur IA", ["OpenAI", "Hugging Face"])

    # --- Section 1 : Société ---
    st.header("Section 1 : Société 👥")
    col1, col2 = st.columns(2)
    with col1:
        scolarisation_primaire = st.text_input("1. Taux de scolarisation primaire (%)")
        scolarisation_secondaire = st.text_input("2. Taux de scolarisation secondaire (%)")
        alphabetisation = st.text_input("3. Taux d’alphabétisation adulte (%)")
        criminalite = st.text_input("4. Taux de criminalité")
    with col2:
        medecins = st.text_input("5. Nombre de médecins pour 10 000 habitants")
        esperance_vie = st.text_input("6. Espérance de vie à la naissance")

    # --- Section 2 : Habitat ---
    st.header("Section 2 : Habitat 🏠")
    col3, col4 = st.columns(2)
    with col3:
        eau = st.text_input("7. Accès à l’eau potable (% population urbaine)")
        electricite = st.text_input("8. Accès à l’électricité (% population urbaine)")
        surpeuplement = st.text_input("9. Qualité du logement (indice de surpeuplement)")
        informel = st.text_input("10. Part des logements informels (%)")
    with col4:
        cout_logement = st.text_input("11. Coût moyen du logement (loyer moyen/m²) en euros")
        accession = st.text_input("12. Taux d’accession à la propriété (%)")
        sanitaires = st.text_input("13. Accès à des sanitaires améliorés (% population)")
        satisfaction = st.text_input("14. Taux de satisfaction des habitants sur leur logement (%)")

    # --- Section 3 : Coordonnées de la Ville ---
    st.header("Section 3 : Coordonnées de la Ville 🏙️📬")
    ville = st.text_input("15. Nom de la Ville 🌆")
    contact = st.text_input("16. Contact de la Ville 📞💻")
    pays = st.text_input("17. Pays 🌍")

    # --- Upload de documents ---
    st.header("Ajoutez vos documents (PDF, CSV, Excel)")
    uploaded_files = st.file_uploader(
        "Vous pouvez ajouter plusieurs fichiers (PDF, CSV, Excel). Leur contenu sera analysé pour enrichir le diagnostic.",
        type=["pdf", "csv", "xlsx"],
        accept_multiple_files=True
    )

    # Lecture du contenu des fichiers (simple, pour démo)
    doc_texts = []
    if uploaded_files:
        st.subheader("📑 Résumé des fichiers uploadés")
        for file in uploaded_files:
            if file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    doc_texts.append(f"Contenu du PDF {file.name} :\n{text[:2000]}")
                    st.markdown(f"**{file.name} (PDF)** : {len(text)} caractères extraits")
                except Exception as e:
                    doc_texts.append(f"Erreur lecture PDF {file.name} : {e}")
                    st.warning(f"Erreur lecture PDF {file.name} : {e}")
            elif file.type == "text/csv":
                df = pd.read_csv(file)
                doc_texts.append(f"Contenu du CSV {file.name} :\n{df.head(10).to_string()}")
                st.dataframe(df.head(5))
            elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df = pd.read_excel(file)
                doc_texts.append(f"Contenu du Excel {file.name} :\n{df.head(10).to_string()}")
                st.dataframe(df.head(5))

    # --- Génération du diagnostic ---
    if st.button("🚀 Générer le diagnostic"):
        st.success(f"✅ Diagnostic en cours de génération pour {ville} ({pays})...")

        # Construction du prompt enrichi
        prompt = f"""
Vous êtes un expert en développement urbain africain. Générez un rapport urbain long, structuré, avec des sous-titres clairs et des recommandations précises, basé sur les informations suivantes :

Section Société :
- Taux de scolarisation primaire : {scolarisation_primaire}
- Taux de scolarisation secondaire : {scolarisation_secondaire}
- Taux d’alphabétisation adulte : {alphabetisation}
- Taux de criminalité : {criminalite}
- Nombre de médecins pour 10 000 habitants : {medecins}
- Espérance de vie à la naissance : {esperance_vie}

Section Habitat :
- Accès à l’eau potable : {eau}
- Accès à l’électricité : {electricite}
- Qualité du logement (surpeuplement) : {surpeuplement}
- Part des logements informels : {informel}
- Coût moyen du logement : {cout_logement}
- Taux d’accession à la propriété : {accession}
- Accès à des sanitaires améliorés : {sanitaires}
- Taux de satisfaction des habitants : {satisfaction}

Coordonnées :
- Ville : {ville}
- Contact : {contact}
- Pays : {pays}

Documents fournis :
{chr(10).join(doc_texts) if doc_texts else "Aucun document fourni."}

Structure du rapport attendue :
1. Résumé exécutif (long, synthétique, avec chiffres clés)
2. Contexte démographique et social (avec analyse fine)
3. Analyse détaillée des défis et opportunités (sous-sections par thème)
4. Recommandations stratégiques (claires, actionnables, adaptées à la ville)
5. Conclusion prospective (scénarios, axes d’amélioration)
6. Références et sources (si possible)

Inclue les informations les plus récentes disponibles sur le web concernant la ville et le pays.
Utilise toutes les informations et documents fournis. Si besoin, complète avec des données publiques récentes sur la ville ou le pays. Mets les sous-titres en gras. Rédige chaque section de façon détaillée et professionnelle.
        """

        rapport = ""
        if moteur_ia == "OpenAI":
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1800,
                    temperature=0.7,
                )
                rapport = response.choices[0].message.content
            except Exception as e:
                rapport = f"Erreur lors de la génération du rapport : {e}"

        elif moteur_ia == "Hugging Face":
            hf_token = st.secrets["HF_TOKEN"]
            with st.spinner("Génération IA Hugging Face en cours..."):
                rapport = generate_hf_report(prompt, hf_token)

        st.markdown("### 🤖 Rapport IA")
        st.markdown(f"""
        <div class="diagnostic-card" style="background:white; padding:1.5rem; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); margin:1rem 0;">
            {rapport}
        </div>
        """, unsafe_allow_html=True)

        # --- Téléchargement PDF ---
        pdf_file = markdown_to_pdf(rapport)
        st.download_button(
            label="📥 Télécharger le rapport en PDF",
            data=pdf_file,
            file_name=f"Diagnostic_{ville}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

# --- ONGLET 2 : DASHBOARD ---
with tab2:
    st.markdown("""
    <div style="background:#f9fbe7; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <b>📊 Visualisez et comparez tous vos diagnostics urbains.</b><br>
        Suivez l’évolution de vos villes et identifiez les leviers d’action.
    </div>
    """, unsafe_allow_html=True)
    st.info("Dashboard à venir : ici s’afficheront tous les diagnostics générés.")

# --- ONGLET 3 : CHATBOT ---
with tab3:
    st.markdown("""
    <div style="background:#e3f2fd; border-radius:8px; padding:1rem; margin-bottom:1rem;">
        <b>💬 Posez vos questions à notre assistant IA !</b><br>
        Obtenez des conseils, des explications et de l’aide sur l’urbanisme.
    </div>
    """, unsafe_allow_html=True)
    question = st.text_input("Posez votre question à l’IA")
    if st.button("Envoyer"):
        if question.strip():
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": question}],
                    max_tokens=300,
                    temperature=0.7,
                )
                reponse_ia = response.choices[0].message.content
            except Exception as e:
                reponse_ia = f"Erreur lors de la réponse IA : {e}"
            st.markdown(f"**Réponse IA :** {reponse_ia}")
        else:
            st.info("Veuillez saisir une question.")
