import json
import mysql.connector
from dotenv import load_dotenv
import os
import re

load_dotenv()

host = os.getenv("MYSQL_HOST")
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")

def clean_text(text):
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.,;:'\"()-]", "", text)
    return text

with open("data/arxiv_full_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

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
    print(f"❌ Erreur connexion MySQL : {e}")
    exit(1)

def insert_affiliation(cursor, name, country, scopus_id):
    cursor.execute("""
        INSERT IGNORE INTO affiliation (scopus_affiliation_id, name, country)
        VALUES (%s, %s, %s)
    """, (scopus_id, name, country))
    cursor.execute("SELECT id FROM affiliation WHERE scopus_affiliation_id = %s", (scopus_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def insert_author(cursor, name, scopus_id, orcid, affiliation_id):
    cursor.execute("""
        INSERT IGNORE INTO author (full_name, scopus_author_id, orcid, main_affiliation_id)
        VALUES (%s, %s, %s, %s)
    """, (name, scopus_id, orcid, affiliation_id))
    cursor.execute("SELECT id FROM author WHERE full_name = %s", (name,))
    row = cursor.fetchone()
    return row[0] if row else None

def insert_article(cursor, title, abstract, year, journal, doi, scopus_id, keywords, subject_areas):
    try:
        year_int = int(year)
    except:
        year_int = None

    cursor.execute("""
        INSERT IGNORE INTO article (title, abstract, publication_year, journal_name,
                                   doi, scopus_identifier, keywords, subject_areas)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (title, abstract, year_int, journal, doi, scopus_id, keywords, subject_areas))
    cursor.execute("SELECT id FROM article WHERE scopus_identifier = %s", (scopus_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def insert_author_article(cursor, author_id, article_id):
    cursor.execute("""
        SELECT id FROM author_article WHERE author_id=%s AND article_id=%s
    """, (author_id, article_id))
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO author_article (author_id, article_id)
            VALUES (%s, %s)
        """, (author_id, article_id))

def insert_affiliation_author(cursor, author_id, affiliation_id):
    cursor.execute("""
        SELECT id FROM affiliation_author WHERE author_id=%s AND affiliation_id=%s
    """, (author_id, affiliation_id))
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO affiliation_author (author_id, affiliation_id)
            VALUES (%s, %s)
        """, (author_id, affiliation_id))

authors_seen = {}
affils_seen = {}
nb_articles = nb_authors = nb_affiliations = 0

for entry in data:
    title = clean_text(entry.get("title", ""))
    abstract = clean_text(entry.get("abstract", ""))
    doi = clean_text(entry.get("doi", "")) if entry.get("doi") else None
    year = clean_text(entry.get("publication_year", ""))
    journal = clean_text(entry.get("journal_name", ""))
    scopus_id = clean_text(entry.get("scopus_identifier", ""))
    keywords = clean_text(entry.get("keywords", ""))
    subject_areas = clean_text(entry.get("subject_areas", ""))

    article_id = insert_article(cursor, title, abstract, year, journal, doi, scopus_id, keywords, subject_areas)
    if article_id:
        nb_articles += 1

    for author in entry.get("authors", []):
        affil = author.get("affiliation", {})
        name_raw = affil.get("name", "")
        country_raw = affil.get("country", "")
        affil_id_raw = affil.get("affiliation_id", "")

        name = clean_text(name_raw)
        country = clean_text(country_raw)
        affil_id = clean_text(affil_id_raw)
        key_affil = affil_id or (name + "|" + country)

        if key_affil and key_affil not in affils_seen:
            db_affil_id = insert_affiliation(cursor, name_raw, country_raw, affil_id_raw)
            affils_seen[key_affil] = db_affil_id
            nb_affiliations += 1

        main_affil_id = affils_seen.get(key_affil)

        full_name = author.get("full_name", "").strip()
        author_name = clean_text(full_name)

        if author_name not in authors_seen:
            author_id = insert_author(cursor, full_name, None, None, main_affil_id)
            if author_id:
                authors_seen[author_name] = author_id
                nb_authors += 1
                print(f"👤 Auteur ajouté : {full_name}")
            else:
                print(f"❌ Auteur NON inséré : {full_name}")
        else:
            author_id = authors_seen[author_name]

        if article_id and author_id:
            insert_author_article(cursor, author_id, article_id)
            if main_affil_id:
                insert_affiliation_author(cursor, author_id, main_affil_id)

cnx.commit()
cursor.close()
cnx.close()

print(f"\n✅ Terminé : {nb_articles} articles, {nb_authors} auteurs, {nb_affiliations} affiliations insérés.")
