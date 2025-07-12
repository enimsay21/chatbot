import faiss
import numpy as np
import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer
import os

class ScopusSearchEngine:
    def __init__(self, index_path='models/scopus_abstracts.index', metadata_path='models/metadata.pkl'):
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError("Les fichiers d'index ou métadonnées n'ont pas été trouvés. "
                                    "Assure-toi que l'index FAISS et les métadonnées sont construits.")
        
        self.index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def search(self, query, k=5):
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.metadata) or idx < 0:
                continue
            item = self.metadata[idx].copy()
             # Formatage des auteurs si nécessaire
        if 'authors' in item and isinstance(item['authors'], list):
            item['authors'] = ', '.join(item['authors'])
            item['similarity_score'] = max(0, 1 - (distance / 4))  # Normalisation simple
            results.append(item)
        
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

class ScopusChatbot:
    def __init__(self):
        self.search_engine = ScopusSearchEngine()

    def process_query(self, query: str) -> str:
        if not query.strip():
            return "Veuillez saisir une question valide."

        results = self.search_engine.search(query, k=5)

        if not results:
            return "Désolé, aucun article correspondant n'a été trouvé."

        response = f"Voici les {len(results)} articles les plus pertinents que j'ai trouvés :\n\n"
        for i, article in enumerate(results, 1):
            title = article.get('title', 'Titre non disponible')
            abstract = article.get('abstract', 'Résumé indisponible')  
            authors = article.get('authors', 'Auteurs inconnus')
            score = article.get('similarity_score', 0)

            response += (
                f"{i}. {title}\n"
                f"Auteurs: {authors}\n"
                f"Résumé: {abstract}\n"
                f"Score de similarité: {score:.2f}\n\n"
            )

        return response



if __name__ == "__main__":
    chatbot = ScopusChatbot()
    while True:
        query = input("Posez votre question scientifique (ou 'exit' pour quitter): ")
        if query.lower() == 'exit':
            break
        answer = chatbot.process_query(query)
        print("\n" + answer + "\n")
