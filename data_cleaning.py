import os
import json
import pandas as pd
from dotenv import load_dotenv
import mysql.connector

# Charger .env
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DATABASE")

if not all([MYSQL_HOST, MYSQL_USER, MYSQL_DB]):
    raise ValueError(" Erreur : une variable d'environnement est manquante. Vérifie ton fichier .env !")

#  Connexion MySQL propre
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
    buffered=True
)

cursor = db.cursor()

#  Chemin du JSON
DATA_PATH = "data/arxiv_data.json"

# Charger JSON dans un DataFrame pandas
with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

df = pd.DataFrame(raw_data)

print(f"Total brut : {len(df)} articles")

#  Nettoyage de base
df.drop_duplicates(subset=['title'], inplace=True)
df.drop_duplicates(subset=['arxiv_identifier'], inplace=True)
df.fillna('', inplace=True)

#  Normalisation texte
text_cols = ['title', 'abstract', 'journal_name', 'doi', 'arxiv_identifier', 'keywords', 'subject_areas', 'pdf_url']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

nb_articles = nb_authors = nb_links = 0

for _, row in df.iterrows():
    title = row['title']
    abstract = row['abstract']
    journal_name = row.get('journal_name', 'ArXiv')
    doi = row.get('doi', None)
    arxiv_id = row['arxiv_identifier']
    keywords = row.get('keywords', '')
    subject_areas = row.get('subject_areas', '')
    pdf_url = row.get('pdf_url', '')

    try:
        publication_year = int(str(row['publication_year'])[:4]) if row['publication_year'] else None
    except:
        publication_year = None

    if not title or not arxiv_id:
        continue

    #  Insertion dans la table article
    try:
        cursor.execute("""
            INSERT IGNORE INTO article
            (title, abstract, publication_year, journal_name, doi, arxiv_identifier, keywords, subject_areas, pdf_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, abstract, publication_year, journal_name, doi, arxiv_id, keywords, subject_areas, pdf_url))
        db.commit()
        nb_articles += cursor.rowcount
    except Exception as e:
        print(f" Erreur insertion article : {e}")
        continue

    # Récupérer l'ID article
    cursor.execute("SELECT id FROM article WHERE arxiv_identifier = %s", (arxiv_id,))
    result = cursor.fetchone()
    article_id = result[0] if result else None
    if not article_id:
        continue

    #  Traitement des auteurs
    authors_list = row.get('authors', [])
    if not isinstance(authors_list, list):
        continue

    clean_authors = set()
    for author in authors_list:
        name = str(author).strip()
        if name:
            clean_authors.add(name)

    for author_name in clean_authors:
        try:
            cursor.execute("""
                INSERT IGNORE INTO author (full_name, arxiv_author_id, orcid, main_affiliation_id)
                VALUES (%s, %s, %s, NULL)
            """, (author_name, None, None))
            db.commit()
            nb_authors += cursor.rowcount
        except Exception as e:
            print(f" Erreur insertion auteur : {e}")
            continue

        cursor.execute("SELECT id FROM author WHERE full_name = %s", (author_name,))
        result = cursor.fetchone()
        author_id = result[0] if result else None
        if not author_id:
            continue

        try:
            cursor.execute("""
                INSERT IGNORE INTO author_article (author_id, article_id)
                VALUES (%s, %s)
            """, (author_id, article_id))
            db.commit()
            nb_links += cursor.rowcount
        except Exception as e:
            print(f" Erreur liaison auteur-article : {e}")
            continue

cursor.close()
db.close()

print(f"Insertion terminée :")
print(f"   Articles insérés : {nb_articles}")
print(f"   Auteurs insérés : {nb_authors}")
print(f"   Liens auteur-article : {nb_links}")
