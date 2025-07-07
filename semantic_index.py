import os
import json
import time
import faiss
import pickle
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ======================= Configuration =======================

# Chargement des variables d'environnement (.env)
load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DATABASE", "chatbot")

# Connexion SQLAlchemy
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}")

# Dossier pour sauvegarder les modèles
os.makedirs("models", exist_ok=True)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================= Classe de Recherche =======================

class SemanticSearch:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.metadata = []

        try:
            self._initialize_model()
            self._build_index()
        except Exception as e:
            logger.error(f"Erreur d'initialisation : {e}")
            raise

    def _initialize_model(self):
        logger.info(f"Chargement du modèle {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Modèle chargé avec succès.")

    def _build_index(self):
        logger.info("🔍 Récupération des articles depuis la base de données...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, title, abstract, publication_year, scopus_identifier, doi, journal_name
                FROM article
                WHERE abstract IS NOT NULL AND abstract != ''
            """))
            articles = result.fetchall()

        if not articles:
            logger.warning("Aucun article trouvé.")
            return

        abstracts = [row.abstract for row in articles]
        self.metadata = [
            {
                "id": row.id,
                "title": row.title,
                "abstract": row.abstract,
                "publication_year": row.publication_year,
                "scopus_identifier": row.scopus_identifier,
                "doi": row.doi,
                "journal_name": row.journal_name
            }
            for row in articles
        ]

        logger.info("🧠 Encodage des résumés...")
        embeddings = self.model.encode(abstracts, show_progress_bar=True, convert_to_numpy=True).astype('float32')
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

        # Sauvegarde des fichiers
        faiss.write_index(self.index, "models/scopus_abstracts.index")
        with open("models/metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f)

        logger.info(f"✅ Index FAISS construit avec {len(self.metadata)} articles.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.index or not self.metadata:
            raise RuntimeError("Index ou métadonnées non initialisés.")

        query_vector = self.model.encode([query], convert_to_numpy=True).astype('float32')
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.metadata):
                continue
            result = self.metadata[idx].copy()
            result['similarity_score'] = max(0, 1 - (distance / 4))
            results.append(result)

        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

# ======================= Exécution =======================

if __name__ == "__main__":
    search_engine = SemanticSearch()
    example_query = "deep learning applications in healthcare"
    results = search_engine.search(example_query, top_k=3)

    print("\n🔎 Résultats de la recherche :")
    for res in results:
        print(f"- {res['title']} ({res['publication_year']}) | Score: {res['similarity_score']:.2f}")
