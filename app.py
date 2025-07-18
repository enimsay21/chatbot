import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from chatbot import ScopusChatbot
import os
from dotenv import load_dotenv
# Charger le fichier .env
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DATABASE")


def detect_years_from_text(text):
    years = re.findall(r'\b(19[5-9]\d|20[0-4]\d|2050)\b', text)
    years = [int(y) for y in years]
    if len(years) >= 2:
        return min(years), max(years)
    elif len(years) == 1:
        return years[0], years[0]
    return None, None

# Style CSS personnalisé
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
    .user-message {
        background: linear-gradient(135deg, #00CED1 0%, #20B2AA 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 5px 18px;
        margin: 1rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 10px rgba(0, 206, 209, 0.3);
    }
   
    .article-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #00CED1;
        margin-bottom: 1rem;
        box-shadow: 0 3px 12px rgba(0, 206, 209, 0.15);
    }
    .article-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #006B6B;
        margin-bottom: 0.5rem;
    }
    .author-tag {
        background: linear-gradient(135deg, #87CEEB 0%, #20B2AA 100%);
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        display: inline-block;
        margin-bottom: 0.3rem;
    }
    .year-badge {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #20B2AA 0%, #48CAE4 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 3px 10px rgba(32, 178, 170, 0.3);
    }
    .filter-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    .page-title {
        background: linear-gradient(135deg, #00CED1 0%, #87CEEB 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class ChatbotDatabase:
    def __init__(self):
        self.db_config = {
            'host': MYSQL_HOST,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'database': MYSQL_DB
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
            
            cursor.execute("SELECT COUNT(*) as total FROM article")
            stats['total_articles'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM author")
            stats['total_authors'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(DISTINCT publication_year) as total FROM article WHERE publication_year IS NOT NULL")
            stats['total_years'] = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT publication_year, COUNT(*) as count 
                FROM article 
                WHERE publication_year IS NOT NULL 
                GROUP BY publication_year 
                ORDER BY publication_year DESC 
                
            """)
            stats['articles_by_year'] = cursor.fetchall()
            
            cursor.execute("""
                SELECT au.full_name, COUNT(*) as count 
                FROM author au
                JOIN author_article aa ON au.id = aa.author_id
                GROUP BY au.id, au.full_name
                ORDER BY count DESC 
               
            """)
            stats['top_authors'] = cursor.fetchall()
            
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

def display_authors(authors):
    if not authors or authors.strip() == "Auteurs inconnus":
        return ""
    
    if isinstance(authors, list):
        authors_list = authors
    elif isinstance(authors, str):
        authors_list = [a.strip() for a in authors.split(',')]
    else:
        return ""

    authors_list = [a for a in authors_list if a and a.lower() != 'none']

    if not authors_list:
        return ""

    author_tags = []
    for author in authors_list[:5]:
        author_tags.append(f'<span class="author-tag">{author}</span>')

    if len(authors_list) > 5:
        author_tags.append(f'<span class="author-tag">+{len(authors_list)-5} autres</span>')

    return ' '.join(author_tags)

def create_word_cloud(text):
    try:
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        words = [word for word in words if word not in stop_words and len(word) > 3]
        
        if words:
            wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='Blues', max_words=50).generate(' '.join(words))
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Erreur lors de la création du nuage de mots: {e}")

def create_visualizations(stats):
    if stats.get('articles_by_year'):
        df_years = pd.DataFrame(stats['articles_by_year'])
        fig_years = px.bar(df_years, x='publication_year', y='count', title='Nombre d\'articles par année', color='count')
        st.plotly_chart(fig_years, use_container_width=True)
    
    if stats.get('top_authors'):
        df_authors = pd.DataFrame(stats['top_authors'][:9])
        fig_authors = px.pie(df_authors, values='count', names='full_name', title='Top Auteurs')
        st.plotly_chart(fig_authors, use_container_width=True)

def page_chatbot():
    st.markdown("""
    <div class="page-title">
        <h1>🤖 Chatbot Scientifique</h1>
        <p>Posez vos questions sur les articles scientifiques</p>
    </div>
    """, unsafe_allow_html=True)
    
    chat_container = st.container()
    with st.form(key='chat_form'):
        user_input = st.text_area("Posez votre question ici :", height=100, key="input")
        submitted = st.form_submit_button("Envoyer")

    if submitted and user_input:
        year_from_detected, year_to_detected = detect_years_from_text(user_input)
        if year_from_detected and year_to_detected:
            st.session_state.filters['year_from'] = year_from_detected
            st.session_state.filters['year_to'] = year_to_detected
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("Recherche en cours..."):
            raw_results = sorted(
            st.session_state.scopus_chatbot.search_engine.search(user_input, k=100),
            key=lambda x: x.get('publication_year', 0),
            reverse=True)
            already_shown = st.session_state.shown_results.get(user_input, [])
            new_results = [article for article in raw_results if article not in already_shown]
            if not new_results:
                new_results = raw_results
                st.session_state.shown_results[user_input] = []
            filtered_results = []
            for article in new_results:
                year_ok = True
                pub_year = article.get('publication_year')
                if pub_year and str(pub_year).isdigit():
                    pub_year = int(pub_year)
                    year_ok = st.session_state.filters['year_from'] <= pub_year <= st.session_state.filters['year_to']
                authors_ok = True
                if st.session_state.filters['authors']:
                    authors = article.get('authors', [])
                    if isinstance(authors, str):
                        authors = [a.strip() for a in authors.split(',')]
                    authors_ok = any(author in authors for author in st.session_state.filters['authors'])
                if year_ok and authors_ok:
                    filtered_results.append(article)
                if len(filtered_results) >= 2:
                    break
            st.session_state.shown_results.setdefault(user_input, []).extend(filtered_results)

            if filtered_results:
                st.session_state.messages.append({"role": "assistant", "content": ""})
            else:
                st.session_state.messages.append({"role": "assistant", "content": " Aucun résultat trouvé avec ces filtres"})

    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">{msg["content"]}</div>', unsafe_allow_html=True)
                if (msg == st.session_state.messages[-1] and 
                    'filtered_results' in locals()):
                    for article in filtered_results[:2]:
                        st.markdown('<div class="article-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="article-title">{article.get("title", "Titre inconnu")}</div>', unsafe_allow_html=True)
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Auteurs:** {display_authors(article.get('authors'))}", unsafe_allow_html=True)
                        with col2:
                            if article.get('publication_year'):
                                st.markdown(f'<span class="year-badge">{article["publication_year"]}</span>', unsafe_allow_html=True)
                        abstract = article.get('abstract', 'Pas de résumé disponible')
                        if abstract != 'Pas de résumé disponible':
                            st.write(f"**Résumé :** {abstract}")
                        if article.get('pdf_url'):
                            st.write(f"**PDF:** [Télécharger le PDF]({article['pdf_url']})")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---")

def page_statistiques():
    st.markdown("""
    <div class="page-title">
        <h1>📈 Statistiques</h1>
        <p>Analyse des données scientifiques</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = init_database()
    stats = db.get_statistics()
    
    if stats:
        # Métriques principales
        cols = st.columns(3)
        cols[0].markdown(f"<div class='metric-card'>Articles<br><b>{stats['total_articles']}</b></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='metric-card'>Auteurs<br><b>{stats['total_authors']}</b></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='metric-card'>Années<br><b>{stats['total_years']}</b></div>", unsafe_allow_html=True)
        
        # Graphiques
        st.header(" Visualisations")
        create_visualizations(stats)
        
        # Nuage de mots
        st.header("☁️ Nuage de mots des titres")
        create_word_cloud(stats.get('titles_text', ''))
    else:
        st.error("Impossible de charger les statistiques")

def page_recherche_avancee():
    st.markdown("""
    <div class="page-title">
        <h1>🔍 Recherche Avancée</h1>
        <p>Recherche détaillée avec filtres</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = init_database()
    
    # Section des filtres
    st.header(" Filtres")
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            years = db.get_years_range()
            year_from = st.number_input("Année minimale", min_value=years[0], max_value=years[1], value=years[0], step=1)
            year_to = st.number_input("Année maximale", min_value=years[0], max_value=years[1], value=years[1], step=1)
        
        with col2:
            authors_list = db.get_authors_list()
            selected_authors = st.multiselect(
                "Sélectionner des auteurs",
                options=authors_list,
                key='advanced_author_filter'
            )
    
    # Section de recherche
    st.header("🔎 Recherche")
    advanced_query = st.text_input("Rechercher un article :", key="advanced_query")
    
    if st.button("Rechercher", type="primary"):
        if not advanced_query.strip():
            st.warning("Veuillez entrer un mot-clé pour la recherche avancée.")
        else:
            with st.spinner("Recherche en cours..."):
                chatbot = ScopusChatbot()
                results = chatbot.search_engine.search(advanced_query, k=50)

                filtered_advanced_results = []
                for article in results:
                    year_ok = True
                    pub_year = article.get('publication_year')
                    if pub_year and str(pub_year).isdigit():
                        pub_year = int(pub_year)
                        year_ok = year_from <= pub_year <= year_to
                    authors_ok = True
                    if selected_authors:
                        authors = article.get('authors', [])
                        if isinstance(authors, str):
                            authors = [a.strip() for a in authors.split(',')]
                        authors_ok = any(author in authors for author in selected_authors)
                    if year_ok and authors_ok:
                        filtered_advanced_results.append(article)

                st.subheader(f"📋 Résultats ({len(filtered_advanced_results)} )")
                if filtered_advanced_results:
                    for article in filtered_advanced_results:
                        st.markdown('<div class="article-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="article-title">{article.get("title", "Titre inconnu")}</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Auteurs:** {display_authors(article.get('authors'))}", unsafe_allow_html=True)
                        with col2:
                            if article.get('publication_year'):
                                st.markdown(f'<span class="year-badge">{article["publication_year"]}</span>', unsafe_allow_html=True)
                        
                        abstract = article.get('abstract', 'Pas de résumé disponible')
                        if abstract != 'Pas de résumé disponible':
                            st.write(f"**Résumé :** {abstract}")
                        if article.get('pdf_url'):
                            st.write(f"**PDF:** [Télécharger le PDF]({article['pdf_url']})")
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.info("Aucun article trouvé avec les critères spécifiés.")

def main():
    # Configuration de la page
    st.set_page_config(
        page_title="Chatbot Scientifique",
        page_icon="🔬",
        layout="wide"
    )
    
    # Initialisation des variables de session
    db = init_database()
    if 'scopus_chatbot' not in st.session_state:
        st.session_state.scopus_chatbot = ScopusChatbot()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'filters' not in st.session_state:
        st.session_state.filters = {'year_from': 2000, 'year_to': 2025, 'authors': []}
    if 'last_question' not in st.session_state:
        st.session_state.last_question = ''
    if 'shown_results' not in st.session_state:
        st.session_state.shown_results = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Chatbot"

    # Sidebar avec navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center;  padding: 2rem; background: linear-gradient(135deg, #00CED1 0%, #87CEEB 200%); border-radius: 10px; margin-bottom: 2rem;">
            <h2 style="color: white; margin: 0;font-weight: bold;">Chatbot Scientifique</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Boutons de navigation
        if st.button("🏠   Chatbot", use_container_width=True):
            st.session_state.current_page = "Chatbot"
        
        if st.button("📊   Statistiques", use_container_width=True):
            st.session_state.current_page = "Statistiques"
        
        if st.button("🔍 Recherche", use_container_width=True):
            st.session_state.current_page = "Recherche Avancée"
        
        st.markdown("---")


    # Affichage de la page sélectionnée
    if st.session_state.current_page == "Chatbot":
        page_chatbot()
    elif st.session_state.current_page == "Statistiques":
        page_statistiques()
    elif st.session_state.current_page == "Recherche Avancée":
        page_recherche_avancee()

if __name__ == "__main__":
    main()