from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import mysql.connector
import pandas as pd
import logging
from typing import List, Dict, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self, db_config: Dict[str, str], model_name: str = 'all-MiniLM-L6-v2'):
        """Initialise le système de recherche sémantique
        
        Args:
            db_config: Configuration de la base de données MySQL
            model_name: Nom du modèle SentenceTransformer à utiliser
        """
        self.db_config = db_config
        self.model_name = model_name
        self.model = None
        self.index = None
        self.articles = []
        
        try:
            self._initialize_model()
            self._build_index()
        except Exception as e:
            logger.error(f"Échec de l'initialisation: {str(e)}")
            raise

    def _initialize_model(self):
        """Charge le modèle SentenceTransformer avec gestion des erreurs"""
        logger.info(f"Chargement du modèle {self.model_name}...")
        try:
            # Vérification préalable des dépendances
            import torch
            if not torch.cuda.is_available():
                logger.warning("CUDA non disponible - Utilisation du CPU")
            
            self.model = SentenceTransformer(
                self.model_name,
                device='cuda' if torch.cuda.is_available() else 'cpu',
                cache_folder='./models'  # Dossier personnalisé pour le cache
            )
            logger.info("Modèle chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            raise

    def _get_connection(self) -> Optional[mysql.connector.MySQLConnection]:
        """Établit une connexion à la base de données"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                connect_timeout=10  # Timeout de connexion
            )
            return conn
        except Exception as e:
            logger.error(f"Échec de la connexion à la DB: {str(e)}")
            return None

    def _build_index(self):
        """Construit l'index FAISS à partir des articles de la base de données"""
        logger.info("Construction de l'index sémantique...")
        
        conn = self._get_connection()
        if not conn:
            raise ConnectionError("Connexion à la base de données échouée")

        try:
            # Requête optimisée avec DISTINCT pour éviter les doublons
            query = """
                SELECT 
                    a.id, 
                    a.title, 
                    a.abstract, 
                    a.publication_year,
                    a.journal_name,
                    a.doi,
                    GROUP_CONCAT(DISTINCT au.full_name SEPARATOR ', ') as authors
                FROM article a
                LEFT JOIN author_article aa ON a.id = aa.article_id
                LEFT JOIN author au ON aa.author_id = au.id
                WHERE a.abstract IS NOT NULL AND a.abstract != ''
                GROUP BY a.id
                HAVING COUNT(a.id) > 0
            """
            
            logger.info("Récupération des articles depuis la base de données...")
            df = pd.read_sql(query, conn)
            
            if df.empty:
                raise ValueError("Aucun article trouvé dans la base de données")
            
            self.articles = df.to_dict('records')
            logger.info(f"{len(self.articles)} articles chargés")

            # Encodage des abstracts
            logger.info("Encodage des articles...")
            embeddings = self.model.encode(
                df['abstract'].tolist(),
                show_progress_bar=True,
                batch_size=32,
                convert_to_numpy=True
            )
            
            # Création de l'index FAISS
            logger.info("Construction de l'index FAISS...")
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings.astype('float32'))
            
            logger.info(f"Index construit avec {self.index.ntotal} vecteurs")

        except Exception as e:
            logger.error(f"Erreur lors de la construction de l'index: {str(e)}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Effectue une recherche sémantique
        
        Args:
            query: Requête textuelle
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste des articles pertinents avec scores de similarité
        """
        if not self.index:
            raise RuntimeError("Index sémantique non initialisé")

        try:
            # Encodage de la requête
            query_embedding = self.model.encode(
                [query],
                show_progress_bar=False,
                convert_to_numpy=True
            ).astype('float32')

            # Recherche dans l'index
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Formatage des résultats
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx >= len(self.articles):
                    continue
                    
                article = self.articles[idx].copy()
                # Normalisation du score entre 0 et 1
                article['similarity_score'] = max(0, 1 - (distance / 4))  
                results.append(article)
            
            # Tri par score décroissant
            return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            raise

    def refresh_index(self):
        """Rafraîchit l'index avec les nouveaux articles"""
        logger.info("Rafraîchissement de l'index...")
        self._build_index()