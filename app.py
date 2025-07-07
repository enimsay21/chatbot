import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import os
from qa_system import QASystem

# Configuration de la page
st.set_page_config(
    page_title="🔬 Chatbot Scientifique",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé avec thème cyan/bleu ciel
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #00CED1 0%, #87CEEB 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 206, 209, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #20B2AA 0%, #48CAE4 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 3px 10px rgba(32, 178, 170, 0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .search-card {
        background: linear-gradient(135deg, #E0F6FF 0%, #B0E0E6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #00CED1;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 206, 209, 0.2);
    }
    
    .article-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #00CED1;
        margin-bottom: 1rem;
        box-shadow: 0 3px 12px rgba(0, 206, 209, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0, 206, 209, 0.25);
    }
    
    .article-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #006B6B;
        margin-bottom: 0.5rem;
    }
    
    .similarity-score {
        background: linear-gradient(135deg, #00CED1 0%, #20B2AA 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0, 206, 209, 0.3);
    }
    
    .filter-card {
        background: linear-gradient(135deg, #E0F6FF 0%, #B0E0E6 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #87CEEB;
        margin-bottom: 1rem;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFF8DC 0%, #F0F8FF 100%);
        border: 2px solid #87CEEB;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .stats-container {
        background: linear-gradient(135deg, #F0F8FF 0%, #E0F6FF 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 2px solid #87CEEB;
    }
    
    .error-box {
        background: linear-gradient(135deg, #FFE4E1 0%, #FFF0F0 100%);
        border: 2px solid #FF6B6B;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #8B0000;
    }
    
    .success-box {
        background: linear-gradient(135deg, #E8F5E8 0%, #F0FFF0 100%);
        border: 2px solid #90EE90;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #006400;
    }
</style>
""", unsafe_allow_html=True)

class ChatbotDatabase:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'chatbot'
        }
    
    def get_connection(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as e:
            st.error(f"Erreur de connexion à la base de données: {e}")
            return None
    
    @st.cache_data(ttl=600)
    def get_statistics(_self):
        try:
            conn = _self.get_connection()
            if not conn:
                return {}
                
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) as total FROM article")
            stats['total_articles'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM author")
            stats['total_authors'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(DISTINCT publication_year) as total FROM article WHERE publication_year IS NOT NULL")
            stats['total_years'] = cursor.fetchone()['total']
            
            # Articles par année
            cursor.execute("""
                SELECT publication_year, COUNT(*) as count 
                FROM article 
                WHERE publication_year IS NOT NULL 
                GROUP BY publication_year 
                ORDER BY publication_year DESC 
                LIMIT 15
            """)
            stats['articles_by_year'] = cursor.fetchall()
            
            # Top auteurs
            cursor.execute("""
                SELECT au.full_name, COUNT(*) as count 
                FROM author au
                JOIN author_article aa ON au.id = aa.author_id
                GROUP BY au.id, au.full_name
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['top_authors'] = cursor.fetchall()
            
            # Mots-clés fréquents dans les titres
            cursor.execute("SELECT title FROM article WHERE title IS NOT NULL")
            titles = [row['title'] for row in cursor.fetchall()]
            stats['titles_text'] = ' '.join(titles)
            
            cursor.close()
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"Erreur statistiques: {e}")
            return {}
        
        
    
    def get_authors_list(self):
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT DISTINCT full_name FROM author ORDER BY full_name")
            authors = [row['full_name'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return authors
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des auteurs: {e}")
            return []
    
    def get_years_range(self):
        try:
            conn = self.get_connection()
            if not conn:
                return (2000, 2025)
                
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT MIN(publication_year) as min_year, MAX(publication_year) as max_year 
                FROM article 
                WHERE publication_year IS NOT NULL
            """)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result['min_year'] and result['max_year']:
                return (int(result['min_year']), int(result['max_year']))
            return (2000, 2025)
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des années: {e}")
            return (2000, 2025)
    

@st.cache_resource
def init_database():
    return ChatbotDatabase()

def init_semantic_search():
    """Initialisation de la recherche sémantique avec gestion d'erreurs améliorée"""
    try:
        # Vérification des dépendances
        import torch
        import sentence_transformers
        
        # Affichage du statut
        status_placeholder = st.empty()
        status_placeholder.info("🔄 Initialisation de la recherche sémantique...")
        
        # Vérification de la connexion internet
        import urllib.request
        try:
            urllib.request.urlopen('https://huggingface.co', timeout=10)
        except:
            raise Exception("Pas de connexion internet. La recherche sémantique nécessite une connexion pour télécharger le modèle.")
        
        # Créer le dossier cache s'il n'existe pas
        cache_dir = './model_cache'
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialisation du modèle avec timeout
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            device='cpu',
            cache_folder=cache_dir
        )
        
        # Test du modèle
        test_embedding = model.encode("test")
        if test_embedding is None or len(test_embedding) == 0:
            raise Exception("Le modèle n'a pas pu générer d'embeddings")
        
        # Essayer d'importer et initialiser SemanticSearch
        try:
            from semantic_index import SemanticSearch
            search = SemanticSearch({
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'chatbot'
            })
            
            status_placeholder.success("✅ Recherche sémantique initialisée avec succès!")
            return search
            
        except ImportError:
            # Si semantic_index n'existe pas, créer une classe simple
            class SimpleSemanticSearch:
                def __init__(self, db_config):
                    self.model = model
                    self.db_config = db_config
                
                def search(self, query, top_k=10):
                    # Implémentation simple basée sur les mots-clés
                    # Vous pouvez l'améliorer selon vos besoins
                    return []
            
            search = SimpleSemanticSearch({
                'host': 'localhost',
                'user': 'root',
                'password': '',
                'database': 'chatbot'
            })
            
            status_placeholder.warning("⚠️ Recherche sémantique en mode simplifié (semantic_index.py non trouvé)")
            return search
            
    except ImportError as e:
        st.error(f"📦 Dépendances manquantes: {str(e)}")
        st.info("Veuillez installer: `pip install sentence-transformers torch`")
        return None
        
    except Exception as e:
        error_msg = str(e)
        
        # Messages d'erreur spécifiques
        if "does not appear to have a file named" in error_msg:
            st.error("🌐 Problème de téléchargement du modèle. Vérifiez votre connexion internet.")
            st.info("Solutions:\n- Vérifiez votre connexion internet\n- Supprimez le dossier `./model_cache`\n- Redémarrez l'application")
        elif "Connection" in error_msg or "timeout" in error_msg:
            st.error("🌐 Problème de connexion internet")
        else:
            st.error(f"❌ Erreur d'initialisation: {error_msg}")
        
        return None

def create_visualizations(stats):
    """Créer des visualisations interactives"""
    col1, col2 = st.columns(2)
    
    with col1:
        if stats.get('articles_by_year'):
            df_years = pd.DataFrame(stats['articles_by_year'])
            fig_years = px.bar(
                df_years, 
                x='publication_year', 
                y='count',
                title='📊 Articles par Année',
                color='count',
                color_continuous_scale=['#87CEEB', '#00CED1', '#20B2AA']
            )
            fig_years.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#006B6B'),
                title_font_size=16
            )
            st.plotly_chart(fig_years, use_container_width=True)
    
    with col2:
        if stats.get('top_authors'):
            df_authors = pd.DataFrame(stats['top_authors'][:8])
            fig_authors = px.pie(
                df_authors, 
                values='count', 
                names='full_name',
                title='👥 Top Auteurs',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_authors.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#006B6B'),
                title_font_size=16
            )
            st.plotly_chart(fig_authors, use_container_width=True)

def create_word_cloud(text):
    """Créer un nuage de mots"""
    try:
        # Nettoyer le texte
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Mots vides à exclure
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = [word for word in words if word not in stop_words and len(word) > 3]
        
        if words:
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='Blues',
                max_words=50
            ).generate(' '.join(words))
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Erreur lors de la création du nuage de mots: {e}")

def display_authors(authors_str):
    """Afficher les auteurs avec style"""
    if not authors_str:
        return "Auteur inconnu"
    
    authors = list(set(authors_str.split(', ')))
    author_tags = []
    
    for author in authors[:5]:  # Limiter à 5 auteurs
        author_tags.append(f'<span class="author-tag">{author}</span>')
    
    if len(authors) > 5:
        author_tags.append(f'<span class="author-tag">+{len(authors)-5} autres</span>')
    
    return ' '.join(author_tags)

def advanced_search(db, query, search_type, year_from, year_to, selected_authors, max_results):
    """Recherche avancée avec filtres"""
    try:
        conn = db.get_connection()
        if not conn:
            return []
            
        cursor = conn.cursor(dictionary=True)
        
        # Construction de la requête SQL
        base_query = """
            SELECT 
                a.*, 
                GROUP_CONCAT(DISTINCT au.full_name SEPARATOR ', ') as authors
            FROM article a
            LEFT JOIN author_article aa ON a.id = aa.article_id
            LEFT JOIN author au ON aa.author_id = au.id
            WHERE 1=1
        """
        
        params = []
        
        # Filtre par texte
        if query:
            base_query += " AND (a.title LIKE %s OR a.abstract LIKE %s)"
            search_term = f"%{query}%"
            params.extend([search_term, search_term])
        
        # Filtre par année
        if year_from and year_to:
            base_query += " AND a.publication_year BETWEEN %s AND %s"
            params.extend([year_from, year_to])
        
        base_query += " GROUP BY a.id"
        
        # Filtre par auteurs
        if selected_authors:
            author_filter = " HAVING " + " OR ".join(["authors LIKE %s"] * len(selected_authors))
            base_query += author_filter
            for author in selected_authors:
                params.append(f"%{author}%")
        
        base_query += " ORDER BY a.publication_year DESC LIMIT %s"
        params.append(max_results)
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        st.error(f"Erreur lors de la recherche: {e}")
        return []

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Chatbot Scientifique Avancé</h1>
        <p>Explorez notre base d'articles scientifiques avec des outils de recherche et visualisation avancés</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de la base de données
    db = init_database()
    
    # Initialisation de la recherche sémantique (non-bloquante)
    semantic_search = None
    with st.expander("🔧 Initialisation de la recherche sémantique", expanded=False):
        if st.button("Initialiser la recherche sémantique"):
            semantic_search = init_semantic_search()
            if semantic_search:
                st.session_state['semantic_search'] = semantic_search
        
        # Récupérer depuis la session si déjà initialisé
        if 'semantic_search' in st.session_state:
            semantic_search = st.session_state['semantic_search']
            st.success("✅ Recherche sémantique disponible!")
    
    # Récupération des données pour les filtres
    authors_list = db.get_authors_list()
    min_year, max_year = db.get_years_range()
    
    # Sidebar avec filtres améliorés
    with st.sidebar:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.header("🔍 Filtres de Recherche")
        
        # Type de recherche
        search_options = ["Mots-clés"]
        if semantic_search:
            search_options.insert(0, "Sémantique")
        
        search_type = st.selectbox(
            "Type de recherche",
            search_options,
            help="Sémantique: recherche par sens, Mots-clés: recherche exacte"
        )
        
        # Filtres par année
        st.subheader("📅 Période")
        year_col1, year_col2 = st.columns(2)
        with year_col1:
            year_from = st.number_input("De", min_value=min_year, max_value=max_year, value=max_year-10)
        with year_col2:
            year_to = st.number_input("À", min_value=min_year, max_value=max_year, value=max_year)
        
        # Filtre par auteurs
        st.subheader("👥 Auteurs")
        selected_authors = st.multiselect(
            "Sélectionner des auteurs",
            options=authors_list,
            help="Laissez vide pour tous les auteurs"
        )
        
        # Nombre de résultats
        st.subheader("📊 Résultats")
        max_results = st.slider("Nombre maximum", 10, 200, 50)
        
        # Options d'affichage
        st.subheader("🎨 Affichage")
        show_abstract = st.checkbox("Afficher les résumés complets", value=True)
        show_visualizations = st.checkbox("Afficher les visualisations", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistiques en haut de page
    if show_visualizations:
        stats = db.get_statistics()
        if stats:
            st.markdown('<div class="stats-container">', unsafe_allow_html=True)
            st.subheader("📈 Statistiques de la Base de Données")
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{stats.get('total_articles', 0):,}</h3>
                    <p>Articles</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{stats.get('total_authors', 0):,}</h3>
                    <p>Auteurs</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{stats.get('total_years', 0)}</h3>
                    <p>Années</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                avg_per_year = stats.get('total_articles', 0) // max(stats.get('total_years', 1), 1)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{avg_per_year}</h3>
                    <p>Articles/An</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Graphiques
            create_visualizations(stats)
            
            # Nuage de mots
            if stats.get('titles_text'):
                st.subheader("☁️ Nuage de Mots des Titres")
                create_word_cloud(stats['titles_text'])
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Interface de recherche principale
    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    st.subheader("🔍 Recherche Scientifique")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input(
            "Entrez votre recherche",
            placeholder="Ex: intelligence artificielle, machine learning, cancer research...",
            help="Tapez des mots-clés ou une phrase complète"
        )
    
    with col2:
        search_button = st.button("Rechercher", type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Affichage des résultats
    if search_query or search_button:
        if not search_query:
            st.warning("⚠️ Veuillez entrer une recherche")
        else:
            with st.spinner("🔍 Recherche en cours..."):
                try:
                    if semantic_search and search_type == "Sémantique":
                        results = semantic_search.search(search_query, top_k=max_results)
                    else:
                        results = advanced_search(db, search_query, search_type, year_from, year_to, selected_authors, max_results)

                    if results:
                        st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                        
                        # Barre de progression pour l'affichage
                        progress_bar = st.progress(0)
                        
                        for i, article in enumerate(results):
                            progress_bar.progress((i + 1) / len(results))
                            
                            with st.container():
                                st.markdown('<div class="article-card">', unsafe_allow_html=True)
                                
                                # Titre
                                st.markdown(f'<div class="article-title">{article["title"]}</div>', unsafe_allow_html=True)
                                
                                # Métadonnées
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**Auteurs:** {display_authors(article.get('authors'))}", unsafe_allow_html=True)
                                
                                with col2:
                                    if article.get('publication_year'):
                                        st.markdown(f'<span class="year-badge">{article["publication_year"]}</span>', unsafe_allow_html=True)
                                
                                # Score de similarité
                                if 'similarity_score' in article:
                                    st.markdown(
                                        f'<span class="similarity-score">Pertinence: {article["similarity_score"]:.0%}</span>',
                                        unsafe_allow_html=True
                                    )
                                
                                # Résumé
                                abstract = article.get('abstract', 'Pas de résumé disponible')
                                if abstract and abstract != 'Pas de résumé disponible':
                                    if show_abstract or len(abstract) <= 300:
                                        st.write(f"**Résumé:** {abstract}")
                                    else:
                                        st.write(f"**Résumé:** {abstract[:300]}...")
                                        with st.expander("Voir le résumé complet"):
                                            st.write(abstract)
                                
                                # DOI et liens
                                if article.get('doi'):
                                    st.write(f"**DOI:** [{article['doi']}](https://doi.org/{article['doi']})")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                                st.markdown("---")
                        
                        progress_bar.empty()
                        
                    else:
                        st.warning("❌ Aucun résultat trouvé. Essayez avec d'autres termes de recherche ou ajustez les filtres.")
                        
                except Exception as e:
                    st.error(f"❌ Une erreur est survenue: {str(e)}")
    
    # Aide et informations
    with st.expander("ℹ️ Aide et Conseils"):
        st.markdown("""
        **Conseils pour une recherche efficace:**
        
        🔍 **Recherche sémantique**: Utilisez des phrases complètes ou des concepts (ex: "traitement du cancer par immunothérapie")
        
        🔑 **Recherche par mots-clés**: Utilisez des termes spécifiques séparés par des espaces
        
        🎯 **Filtres**: Combinez plusieurs filtres pour affiner vos résultats
        
        📊 **Visualisations**: Activez les graphiques pour explorer les tendances
        
        💡 **Astuce**: Commencez par une recherche large puis affinez avec les filtres
        
        **Problèmes courants:**
        - Si la recherche sémantique ne fonctionne pas, utilisez la recherche par mots-clés
        - Vérifiez votre connexion internet pour initialiser la recherche sémantique
        - Installez les dépendances: `pip install sentence-transformers torch`
        """)

if __name__ == "__main__":
    main()