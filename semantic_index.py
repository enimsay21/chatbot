import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

USER = os.getenv("MYSQL_USER")
PASSWORD = os.getenv("MYSQL_PASSWORD")
HOST = os.getenv("MYSQL_HOST")
DB = os.getenv("MYSQL_DATABASE")

# Créer la connexion SQLAlchemy
engine = create_engine(f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB}")

def build_faiss_index():
    print("🔎 Chargement du modèle...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Récupérer les articles avec les colonnes nécessaires
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, title, abstract, publication_year, scopus_identifier, doi, journal_name
            FROM article
            WHERE abstract IS NOT NULL AND abstract != ''
        """))
        articles = result.fetchall()

    if not articles:
        print("❌ Aucun article trouvé.")
        return

    # Extraire les données
    ids = []
    abstracts = []
    metadata = []

    for row in articles:
        ids.append(row.id)
        abstracts.append(row.abstract)
        metadata.append({
            "id": row.id,
            "title": row.title,
            "abstract": row.abstract,
            "publication_year": row.publication_year,
            "scopus_identifier": row.scopus_identifier,
            "doi": row.doi,
            "journal_name": row.journal_name
        })

    print("🧠 Encodage des résumés...")
    embeddings = model.encode(abstracts, show_progress_bar=True)
    dim = embeddings.shape[1]

    print("📦 Construction de l'index FAISS...")
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype('float32'))

    # Sauvegarder l'index FAISS
    faiss.write_index(index, "models/scopus_abstracts.index")
    
    # Sauvegarder les métadonnées enrichies
    with open("models/metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ Index FAISS créé avec {len(metadata)} articles et métadonnées enrichies.")

if __name__ == "__main__":
    build_faiss_index()
