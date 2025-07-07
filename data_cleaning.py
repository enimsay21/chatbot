import json
import mysql.connector

# Connexion à la base avec buffered=True
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="chatbot",
    buffered=True
)

DATA_PATH = "data/my_data.json"

# Lecture des données
with open(DATA_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)

nb_articles = 0
nb_auteurs = 0
nb_liaisons = 0

for article in articles:
    title = article.get("title", "").strip()
    abstract = article.get("abstract", "").strip()
    journal_name = article.get("journal_name", "").strip()
    doi = article.get("doi", "").strip()
    scopus_id = article.get("scopus_id", "").strip()
    keywords = article.get("keywords", "").strip()
    subject_areas = article.get("subject_areas", "").strip()

    # Gestion de l'année
    publication_year = article.get("publication_year")
    try:
        publication_year = int(publication_year[:4]) if publication_year else None
    except:
        publication_year = None

    # Insertion Article
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT IGNORE INTO article 
                (title, abstract, publication_year, journal_name, doi, scopus_identifier, keywords, subject_areas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, abstract, publication_year, journal_name, doi, scopus_id, keywords, subject_areas))
            db.commit()
            nb_articles += 1
    except Exception as e:
        print(f"❌ Erreur insertion article : {e}")
        continue

    # Récupération de l'ID Article
    article_id = None
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM article WHERE scopus_identifier = %s", (scopus_id,))
            result = cursor.fetchone()
            if result:
                article_id = result[0]
    except Exception as e:
        print(f"⚠️ Erreur récupération article : {e}")
        continue

    if not article_id:
        continue

    # Insertion des Auteurs
    for author_name in article.get("authors", []):
        author_name = author_name.strip()
        if not author_name:
            continue

        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    INSERT IGNORE INTO author (full_name, scopus_author_id, orcid, main_affiliation_id)
                    VALUES (%s, %s, %s, NULL)
                """, (author_name, None, None))
                db.commit()
                nb_auteurs += 1
        except Exception as e:
            print(f"❌ Erreur insertion auteur : {e}")
            continue

        author_id = None
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT id FROM author WHERE full_name = %s", (author_name,))
                result = cursor.fetchone()
                if result:
                    author_id = result[0]
        except Exception as e:
            print(f"⚠️ Erreur récupération auteur : {e}")
            continue

        if not author_id:
            continue

        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    INSERT IGNORE INTO author_article (author_id, article_id)
                    VALUES (%s, %s)
                """, (author_id, article_id))
                db.commit()
                nb_liaisons += 1
        except Exception as e:
            print(f"❌ Erreur liaison auteur-article : {e}")
            continue

db.close()
print(f"\n✅ Insertion terminée : {nb_articles} articles, {nb_auteurs} auteurs, {nb_liaisons} liaisons.")