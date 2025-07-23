import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import base64
import matplotlib.pyplot as plt
from io import BytesIO

def extract_text_from_image_pdf(pdf_file):
    try:
        images = convert_from_bytes(pdf_file.read(), dpi=200)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"[Erreur OCR] : {e}"

def generate_graph_base64():
    try:
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [2, 5, 3])
        ax.set_title("Indice synthétique de qualité urbaine")
        buf = BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as e:
        return ""
