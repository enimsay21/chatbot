import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np
import os

class QASystem:
    def __init__(self):
        self.model = None
        self.qa_pipeline = None
        self.embedding_model = None
        self.cache_dir = './model_cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def initialize(self):
        """Initialise les modèles de Q&A"""
        try:
            # Modèle pour les embeddings
            self.embedding_model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device='cpu',
                cache_folder=self.cache_dir
            )
            
            # Modèle de question-réponse
            self.qa_pipeline = pipeline(
                'question-answering',
                model='deepset/roberta-base-squad2',
                tokenizer='deepset/roberta-base-squad2',
                device='cpu'
            )
            
            return True
        except Exception as e:
            print(f"Erreur d'initialisation: {e}")
            return False
    
    def extract_relevant_context(self, question: str, documents: List[Dict], top_k: int = 3) -> List[str]:
        """Extrait les passages les plus pertinents pour la question"""
        try:
            # Embedding de la question
            question_embedding = self.embedding_model.encode(question)
            
            # Calcul des similarités
            similarities = []
            for doc in documents:
                text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
                doc_embedding = self.embedding_model.encode(text)
                similarity = np.dot(question_embedding, doc_embedding) / (
                    np.linalg.norm(question_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append(similarity)
            
            # Tri des documents par pertinence
            sorted_indices = np.argsort(similarities)[::-1][:top_k]
            contexts = []
            for idx in sorted_indices:
                contexts.append(f"Titre: {documents[idx].get('title', '')}\nRésumé: {documents[idx].get('abstract', '')}")
            
            return contexts
        except Exception as e:
            print(f"Erreur d'extraction de contexte: {e}")
            return []
    
    def answer_question(self, question: str, context: str) -> Dict:
        """Répond à une question basée sur un contexte"""
        try:
            if not self.qa_pipeline:
                return {"error": "Système Q&A non initialisé"}
                
            result = self.qa_pipeline({
                'question': question,
                'context': context[:10000]  # Limite de contexte pour le modèle
            })
            
            return {
                'answer': result['answer'],
                'score': result['score'],
                'start': result['start'],
                'end': result['end']
            }
        except Exception as e:
            return {"error": str(e)}