import requests
import json

def generate_ollama_report(prompt):
    """Utilise Ollama en local (gratuit)"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama2',  # ou 'mistral', 'codellama'
                'prompt': prompt,
                'stream': False
            }
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Erreur Ollama: {response.text}"
    except Exception as e:
        return f"Ollama non disponible: {e}. Installez Ollama depuis https://ollama.ai"

# Dans votre interface, ajoutez cette option :
moteur_ia = st.selectbox("Choisissez le moteur IA", ["OpenAI", "Hugging Face", "Ollama (Local)"])

# Dans la génération du rapport :
elif moteur_ia == "Ollama (Local)":
    with st.spinner("Génération IA Ollama en cours..."):
        rapport = generate_ollama_report(prompt)
