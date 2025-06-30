import pandas as pd
import json
import mysql.connector
from dotenv import load_dotenv
import os
import re

# Charger les variables d’environnement
load_dotenv()
host = os.getenv("MYSQL_HOST")
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")

# Charger les données JSON
with open("data/scopus_data.json", "r", encoding="utf-8") as f:
    results = json.load(f)

df = pd.json_normalize(results)

# Affichage des colonnes pour debug
print("📋 Colonnes originales :", df.columns.tolist())

# Renommage si nécessaire
if "scopus_id" in df.columns:
    df.rename(columns={"scopus_id": "scopus_identifier"}, inplace=True)

# Vérifier que les colonnes attendues existent, sinon les créer vides
expected_cols = [
    "title", "abstract", "publication_year", "journal_name",
    "doi", "scopus_identifier", "keywords", "subject_areas", "authors", "affiliations"
]
for col in expected_cols:
    if col not in df.columns:
        df[col] = ""

# Nettoyage des données
df.fillna("", inplace=True)
df["title"] = df["title"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
df["abstract"] = df["abstract"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
df["journal_name"] = df["journal_name"].astype(str).str.strip()
df["keywords"] = df["keywords"].astype(str).str.strip()
df["doi"] = df["doi"].astype(str).str.strip()
df["publication_year"] = df["publication_year"].astype(str).str.extract(r"(\d{4})")
df["subject_areas"] = df["subject_areas"].astype(str)
df.drop_duplicates(subset="scopus_identifier", inplace=True)

# Connexion à la base de données
try:
    cnx = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = cnx.cursor()
    print("✅ Connexion MySQL réussie.")
except Exception as e:
    print(f"❌ Connexion échouée : {e}")
    exit(1)

# Fonctions d'insertion SQL
def insert_affiliation(cursor, name, country, scopus_affil_id):
    try:
        cursor.execute("""
            INSERT IGNORE INTO affiliation (name, country, scopus_affiliation_id)
            VALUES (%s, %s, %s)
        """, (name, country, scopus_affil_id))
        cursor.execute("SELECT id FROM affiliation WHERE scopus_affiliation_id = %s", (scopus_affil_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur insert_affiliation: {e}")
        return None

def insert_author(cursor, name, scopus_id, orcid, affiliation_id):
    try:
        name = name.strip().title()
        cursor.execute("""
            INSERT IGNORE INTO author (full_name, scopus_author_id, orcid, main_affiliation_id)
            VALUES (%s, %s, %s, %s)
        """, (name, scopus_id, orcid, affiliation_id))
        cursor.execute("SELECT id FROM author WHERE scopus_author_id = %s", (scopus_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur insert_author: {e}")
        return None

def insert_article(cursor, title, abstract, year, journal, doi, identifier, keywords, subjects):
    try:
        cursor.execute("""
            INSERT IGNORE INTO article (title, abstract, publication_year, journal_name,
            doi, scopus_identifier, keywords, subject_areas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, abstract, year, journal, doi, identifier, keywords, subjects))
        cursor.execute("SELECT id FROM article WHERE scopus_identifier = %s", (identifier,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Erreur insert_article: {e}")
        return None

# Insertion des données
print("⏳ Début insertion...")

nb_articles = 0
nb_authors = 0

for i, (_, row) in enumerate(df.iterrows(), 1):
    print(f"📄 Article {i}/{len(df)} : {row['title'][:50]}...")

    article_id = insert_article(
        cursor,
        row['title'], row['abstract'], row['publication_year'],
        row['journal_name'], row['doi'], row['scopus_identifier'],
        row['keywords'], row['subject_areas']
    )
    if article_id:
        nb_articles += 1

    authors = row.get("authors", [])
    affiliations = row.get("affiliations", [])

    if not isinstance(authors, list):
        print(f"⚠️ Ligne {i}: 'authors' n'est pas une liste.")
        authors = []

    if not isinstance(affiliations, list):
        affiliations = []

    for author in authors:
        if not isinstance(author, dict):
            continue

        name = author.get("authname", "")
        scopus_author_id = author.get("@auid", "")
        orcid = author.get("orcid", "")
        aff_id = None

        for aff in affiliations:
            if isinstance(aff, dict):
                affname = aff.get("affilname", "")
                country = aff.get("affiliation-country", "")
                aff_scopus_id = aff.get("@id", "")
                aff_id = insert_affiliation(cursor, affname, country, aff_scopus_id)
                break

        author_id = insert_author(cursor, name, scopus_author_id, orcid, aff_id)
        if author_id:
            nb_authors += 1

        if article_id and author_id:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO author_article (author_id, article_id)
                    VALUES (%s, %s)
                """, (author_id, article_id))
                if aff_id:
                    cursor.execute("""
                        INSERT IGNORE INTO affiliation_author (author_id, affiliation_id)
                        VALUES (%s, %s)
                    """, (author_id, aff_id))
            except Exception as e:
                print(f"Erreur lien auteur-article ou affiliation: {e}")

cnx.commit()
print(f"✅ Insertion terminée : {nb_articles} articles, {nb_authors} auteurs.")
cursor.close()
cnx.close()
print("🔒 Connexion fermée.")
