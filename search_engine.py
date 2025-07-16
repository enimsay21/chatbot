import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

class ScopusSearchEngine:
    def __init__(self, index_path='models/arxiv_abstracts.index', metadata_path='models/metadata.pkl'):
        self.index = faiss.read_index(index_path)
        self.metadata = pd.read_pickle(metadata_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def search(self, query, k=5):
        query_embedding = self.model.encode([query]).astype('float32')
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.metadata):
                row = self.metadata[idx] if isinstance(self.metadata, list) else self.metadata.iloc[idx]
                result = {
                    "title": row.get("title", "Titre inconnu"),
                    "abstract": row.get("abstract", "Résumé indisponible"),
                    "authors": ', '.join(row["authors"]) if isinstance(row.get("authors"), list) else row.get("authors", "Auteurs inconnus"),
                    "publication_year": row.get("publication_year", "Année inconnue"),
                    "pdf_url": row.get("pdf_url", None),
                    "similarity_score": max(0, 1 - (distance / 4))
                }
                results.append(result)

        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)
