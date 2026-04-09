import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification, LayoutLMv2ForTokenClassification
from sentence_transformers import SentenceTransformer
import spacy
from spacy.cli import download

# Define local cache directory
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'local_models')
os.makedirs(MODELS_DIR, exist_ok=True)

def download_huggingface_models():
    print("Downloading Sentence Transformer (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.save(os.path.join(MODELS_DIR, 'all-MiniLM-L6-v2'))

    print("Downloading DistilBERT (distilbert-base-uncased)...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
    tokenizer.save_pretrained(os.path.join(MODELS_DIR, 'distilbert-base-uncased'))
    model.save_pretrained(os.path.join(MODELS_DIR, 'distilbert-base-uncased'))

    print("Downloading LayoutLM (microsoft/layoutlm-base-uncased)...")
    # For extraction tasks, LayoutLM token classification is often used
    tokenizer2 = AutoTokenizer.from_pretrained("microsoft/layoutlm-base-uncased")
    model2 = AutoModelForTokenClassification.from_pretrained("microsoft/layoutlm-base-uncased")
    tokenizer2.save_pretrained(os.path.join(MODELS_DIR, 'layoutlm-base-uncased'))
    model2.save_pretrained(os.path.join(MODELS_DIR, 'layoutlm-base-uncased'))
    
def download_spacy_models():
    print("Downloading spaCy basic English model (en_core_web_sm)...")
    try:
        spacy.load("en_core_web_sm")
        print("en_core_web_sm already installed.")
    except Exception:
        download("en_core_web_sm")

if __name__ == "__main__":
    print(f"Models will be stored in: {MODELS_DIR}")
    download_spacy_models()
    download_huggingface_models()
    print("All downloads complete! The system is ready for offline operation.")
