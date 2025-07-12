import os
import pickle
import logging
import faiss

from dotenv import load_dotenv
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer


# Charger les variables d'environnement
load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DATABASE")

# Vérification
if not all([MYSQL_USER, MYSQL_PASSWORD is not None, MYSQL_HOST, MYSQL_DB]):
    raise EnvironmentError(" Erreur : variables .env manquantes ou mal définies (MYSQL_USER, MYSQL_PASSWORD, etc.)")

# Connexion SQLAlchemy
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}")

# Créer dossier pour les modèles
os.makedirs("models", exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Classe SemanticSearch

class SemanticSearch:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.metadata = []
        self._build_index()

    def _build_index(self):
        logger.info("Récupération des articles depuis la base MySQL...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, title, abstract, publication_year, scopus_identifier, doi, journal_name, pdf_url
                FROM article
                WHERE abstract IS NOT NULL AND abstract != ''
            """))
            articles = result.fetchall()

        if not articles:
            logger.warning(" Aucun article trouvé.")
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
                "journal_name": row.journal_name,
                "pdf_url": row.pdf_url
            }
            for row in articles
        ]

        logger.info(" Encodage des résumés avec le modèle NLP...")
        embeddings = self.model.encode(abstracts, show_progress_bar=True, convert_to_numpy=True).astype("float32")
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

        # Sauvegarde
        faiss.write_index(self.index, "models/scopus_abstracts.index")
        with open("models/metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f)

        logger.info(f"✅ Index FAISS créé avec {len(self.metadata)} articles.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None or not self.metadata:
            raise RuntimeError(" L’index n’est pas initialisé.")

        logger.info(f" Requête utilisateur : {query}")
        query_vector = self.model.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.metadata):
                continue
            article = self.metadata[idx].copy()
            article["similarity_score"] = max(0, 1 - (distance / 4))  # Normalisation possible
            results.append(article)

        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)

# execute

if __name__ == "__main__":
    search_engine = SemanticSearch()
    query = "deep learning in medicine"
    results = search_engine.search(query, top_k=3)

    print("\n Résultats de la recherche :")
    for res in results:
        print(f"- {res['title']} ({res['publication_year']}) | Score: {res['similarity_score']:.2f}")
        if res.get("pdf_url"):
            print(f"   PDF: {res['pdf_url']}")
