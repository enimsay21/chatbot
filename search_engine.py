import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

class ScopusSearchEngine:
    def __init__(self, index_path='models/scopus_abstracts.index', metadata_path='models/metadata.pkl'):
        # Charger l'index FAISS
        self.index = faiss.read_index(index_path)

        # Charger les métadonnées
        self.metadata = pd.read_pickle(metadata_path)

        # Vérifier les colonnes présentes
        print("Colonnes trouvées :", self.metadata.columns.tolist())

        # Initialiser SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def search(self, query, k=5):
        # Encoder la requête
        query_embedding = self.model.encode([query]).astype('float32')

        # Recherche dans FAISS
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.metadata):
                row = self.metadata.iloc[idx]

                result = {
                    "title": row.get("title", "Titre inconnu"),
                    "abstract": row.get("abstract", "Résumé indisponible"),
                    "authors": row.get("authors", "Auteurs inconnus"),
                    "publication_year": row.get("publication_year", "Année inconnue"),
                    "pdf_url": row.get("pdf_url", None), 
                    "similarity_score": 1 - distance
                }

                results.append(result)

        # Trier par similarité décroissante
        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)
