
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

class ScopusSearchEngine:
    def __init__(self, index_path='models/scopus_abstracts.index', metadata_path='models/metadata.pkl'):
        self.index = faiss.read_index(index_path)
        self.metadata = pd.read_pickle(metadata_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def search(self, query, k=5):
        # Convertir la requête en embedding
        query_embedding = self.model.encode([query])
        
        # Rechercher les k articles les plus proches
        distances, indices = self.index.search(query_embedding, k)
        
        # Récupérer les résultats
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= 0:  # -1 signifie aucun résultat
                result = self.metadata.iloc[idx].to_dict()
                result['similarity_score'] = 1 - distance  # Convertir distance en similarité
                results.append(result)
                
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
