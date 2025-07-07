import json
import mysql.connector

# Connexion à la base
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="chatbot",
    buffered=True
)

DATA_PATH = "data/arxiv_data.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)

nb_articles = 0  # → Compte tous les articles extraits
nb_articles_inserts = 0  # → Compte les nouvelles insertions réelles
nb_auteurs = 0
nb_liaisons = 0

cursor = db.cursor()

def safe_strip(value):
    if value is None:
        return ""
    return str(value).strip()

for article in articles:
    nb_articles += 1  # ✅ Compte chaque article parcouru

    title = safe_strip(article.get("title"))
    abstract = safe_strip(article.get("abstract"))
    journal_name = safe_strip(article.get("journal_name"))
    doi = safe_strip(article.get("doi"))
    scopus_id = safe_strip(article.get("scopus_id"))
    keywords = safe_strip(article.get("keywords"))
    subject_areas = safe_strip(article.get("subject_areas"))

    publication_year = article.get("publication_year")
    try:
        publication_year = int(str(publication_year)[:4]) if publication_year else None
    except Exception:
        publication_year = None

    try:
        cursor.execute("""
            INSERT IGNORE INTO article 
            (title, abstract, publication_year, journal_name, doi, scopus_identifier, keywords, subject_areas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, abstract, publication_year, journal_name, doi, scopus_id, keywords, subject_areas))
        db.commit()
        if cursor.rowcount > 0:
            nb_articles_inserts += 1
    except Exception as e:
        print(f"❌ Erreur insertion article : {e}")
        continue

    try:
        cursor.execute("SELECT id FROM article WHERE scopus_identifier = %s", (scopus_id,))
        result = cursor.fetchone()
        article_id = result[0] if result else None
    except Exception as e:
        print(f"⚠️ Erreur récupération article : {e}")
        continue

    if not article_id:
        continue

    authors_list = article.get("authors", [])
    if isinstance(authors_list, dict):
        authors_list = []

    for author_name in authors_list:
        author_name = safe_strip(author_name)
        if not author_name:
            continue

        try:
            cursor.execute("""
                INSERT IGNORE INTO author (full_name, scopus_author_id, orcid, main_affiliation_id)
                VALUES (%s, %s, %s, NULL)
            """, (author_name, None, None))
            db.commit()
            nb_auteurs += cursor.rowcount
        except Exception as e:
            print(f"❌ Erreur insertion auteur : {e}")
            continue

        try:
            cursor.execute("SELECT id FROM author WHERE full_name = %s", (author_name,))
            result = cursor.fetchone()
            author_id = result[0] if result else None
        except Exception as e:
            print(f"⚠️ Erreur récupération auteur : {e}")
            continue

        if not author_id:
            continue

        try:
            cursor.execute("""
                INSERT IGNORE INTO author_article (author_id, article_id)
                VALUES (%s, %s)
            """, (author_id, article_id))
            db.commit()
            nb_liaisons += cursor.rowcount
        except Exception as e:
            print(f"❌ Erreur liaison auteur-article : {e}")
            continue

cursor.close()
db.close()

print(f"\n✅ Insertion terminée : {nb_articles} articles traités, {nb_articles_inserts} nouveaux articles insérés, {nb_auteurs} auteurs insérés, {nb_liaisons} liaisons créées.")
