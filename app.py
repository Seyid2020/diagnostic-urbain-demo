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
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import matplotlib.pyplot as plt
import base64

# --- OCR pour PDF scannés ---
def extract_text_from_image_pdf(pdf_file):
    try:
        images = convert_from_bytes(pdf_file.read(), dpi=200)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"[Erreur OCR] : {e}"

# --- Génération graphique simple ---
def generate_graph_base64():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [10, 20, 15, 30])
    ax.set_title("Indice synthétique de qualité urbaine")
    buf = BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# --- Fonction Hugging Face ---
def generate_hf_report(prompt, hf_token):
    from huggingface_hub import InferenceClient
    try:
        client = InferenceClient(api_key=hf_token)
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur Hugging Face Providers: {e}"

# --- Fonction Groq ---
def generate_groq_report(prompt, groq_api_key, model="llama3-70b-8192"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1800,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Erreur Groq: {response.text}"

# --- Convert Markdown to PDF ---
def markdown_to_pdf(text):
    plain_text = markdown.markdown(text)
    import re
    plain_text = re.sub('<[^<]+?>', '', plain_text)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    lines = simpleSplit(plain_text, 'Helvetica', 12, width - 2 * margin)
    for line in lines:
        if y < margin:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line)
        y -= 15
    c.save()
    buffer.seek(0)
    return buffer

# --- UI Accueil ---
st.markdown("""
<div class="logo-container">
    <img src="https://cdn.abacus.ai/images/d1788567-27c2-4731-b4f0-26dc07fcd4f3.png" alt="CUS Logo" width="320">
</div>
<div class="main-header">
    <h1 style="color:#1f4e79;">🏙️ UrbanAI Diagnostic</h1>
    <h3 style="color:#e67e22;">La plateforme intelligente pour le diagnostic urbain en Afrique</h3>
    <p style="font-size:1.1rem; color:#34495e;">
        <b>Description :</b> Diagnostic rapide, interactif et enrichi par l'IA, basé sur vos réponses et vos documents.
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🆕 Nouveau Diagnostic", "📊 Dashboard", "💬 Chatbot"])

with tab1:
    st.header("Section 1 : Société 👥")
    col1, col2 = st.columns(2)
    with col1:
        scolarisation_primaire = st.text_input("Taux de scolarisation primaire (%)")
        scolarisation_secondaire = st.text_input("Taux de scolarisation secondaire (%)")
        alphabetisation = st.text_input("Taux d'alphabétisation adulte (%)")
        criminalite = st.text_input("Taux de criminalité")
    with col2:
        medecins = st.text_input("Nombre de médecins / 10k habitants")
        esperance_vie = st.text_input("Espérance de vie")

    st.header("Section 2 : Habitat 🏠")
    col3, col4 = st.columns(2)
    with col3:
        eau = st.text_input("Accès à l'eau potable (%)")
        electricite = st.text_input("Accès à l'électricité (%)")
        surpeuplement = st.text_input("Indice de surpeuplement")
        informel = st.text_input("Logements informels (%)")
    with col4:
        cout_logement = st.text_input("Coût moyen du logement (€/m²)")
        accession = st.text_input("Taux d'accession à la propriété (%)")
        sanitaires = st.text_input("Accès à des sanitaires améliorés (%)")
        satisfaction = st.text_input("Satisfaction logement (%)")

    st.header("Section 3 : Ville 📍")
    ville = st.text_input("Nom de la Ville")
    contact = st.text_input("Contact")
    pays = st.text_input("Pays")

    st.header("Ajoutez vos documents (PDF, CSV, Excel)")
    uploaded_files = st.file_uploader("Fichiers support", type=["pdf", "csv", "xlsx"], accept_multiple_files=True)

    doc_texts = []
    if uploaded_files:
        for file in uploaded_files:
            if file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(file)
                    text = "".join([p.extract_text() or "" for p in reader.pages])
                    if len(text.strip()) < 50:
                        file.seek(0)
                        text = extract_text_from_image_pdf(file)
                    doc_texts.append(f"Contenu du PDF {file.name} :\n{text[:2000]}")
                except Exception as e:
                    doc_texts.append(f"Erreur lecture PDF {file.name} : {e}")
            elif file.type == "text/csv":
                df = pd.read_csv(file)
                doc_texts.append(f"CSV {file.name} :\n{df.head().to_string()}")
            elif file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df = pd.read_excel(file)
                doc_texts.append(f"Excel {file.name} :\n{df.head().to_string()}")

    moteur_ia = st.selectbox("Moteur IA", ["OpenAI", "Hugging Face", "Groq"])

    if st.button("🚀 Générer le diagnostic"):
        st.info("Génération du rapport IA...")

        prompt = f"""
Vous êtes un expert en développement urbain africain. Rédigez un rapport structuré et détaillé basé sur :

Section Société :
- Scolarisation primaire : {scolarisation_primaire}
- Scolarisation secondaire : {scolarisation_secondaire}
- Alphabétisation : {alphabetisation}
- Criminalité : {criminalite}
- Médecins : {medecins}
- Espérance de vie : {esperance_vie}

Section Habitat :
- Eau potable : {eau}
- Électricité : {electricite}
- Surpeuplement : {surpeuplement}
- Logements informels : {informel}
- Coût logement : {cout_logement}
- Accession : {accession}
- Sanitaires : {sanitaires}
- Satisfaction : {satisfaction}

Coordonnées :
- Ville : {ville}
- Contact : {contact}
- Pays : {pays}

Documents :
{chr(10).join(doc_texts) if doc_texts else "Aucun"}

Structure :
1. Résumé exécutif
2. Contexte démographique et social
3. Défis & opportunités
4. Recommandations
5. Conclusion
        """

        if moteur_ia == "OpenAI":
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1800,
                temperature=0.7,
            )
            rapport = response.choices[0].message.content
        elif moteur_ia == "Hugging Face":
            rapport = generate_hf_report(prompt, st.secrets["HF_TOKEN"])
        elif moteur_ia == "Groq":
            rapport = generate_groq_report(prompt, st.secrets["GROQ_API_KEY"])

        st.markdown("### 🧠 Rapport IA généré")
        st.markdown(rapport)

        st.download_button(
            label="📥 Télécharger en PDF",
            data=markdown_to_pdf(rapport),
            file_name=f"Diagnostic_{ville}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

        img_base64 = generate_graph_base64()
        st.markdown("### 📈 Graphique indicatif")
        st.markdown(f'<img src="data:image/png;base64,{img_base64}" width="500">', unsafe_allow_html=True)

with tab2:
    st.info("Dashboard à venir...")

with tab3:
    question = st.text_input("Posez votre question à l’IA")
    if st.button("Envoyer"):
        if question.strip():
            if moteur_ia == "Groq":
                reponse = generate_groq_report(question, st.secrets["GROQ_API_KEY"], model="llama3-8b-8192")
            else:
                client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": question}],
                    max_tokens=300,
                    temperature=0.7,
                )
                reponse = response.choices[0].message.content
            st.markdown(f"**Réponse IA :** {reponse}")
