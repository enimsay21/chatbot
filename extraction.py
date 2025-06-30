# extract_scopus.py

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SCOPUS_API_KEY")

if not API_KEY:
    raise ValueError("❌ SCOPUS_API_KEY non trouvée dans .env")

SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
DETAILS_URL = "https://api.elsevier.com/content/abstract/scopus_id/"

HEADERS = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json"
}

def search_scopus(query, max_results=100, count_per_page=25):
    results = []
    start = 0

    while start < max_results:
        params = {"query": query, "count": count_per_page, "start": start}
        print(f"🔎 Extraction {start} à {start + count_per_page}")
        resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)

        if resp.status_code != 200:
            print("❌ Erreur API:", resp.status_code)
            break

        entries = resp.json().get("search-results", {}).get("entry", [])
        if not entries:
            break

        results.extend(entries)
        start += count_per_page
        time.sleep(1)

    return results

def get_article_details(scopus_id):
    url = f"{DETAILS_URL}{scopus_id}"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"⚠️ Article {scopus_id} non détaillé.")
        return {}

    data = resp.json().get("abstracts-retrieval-response", {})

    title = data.get("core", {}).get("dc:title", "")
    abstract = data.get("core", {}).get("dc:description", "")
    doi = data.get("core", {}).get("prism:doi", "")
    publication = data.get("core", {}).get("prism:publicationName", "")
    year = data.get("core", {}).get("prism:coverDate", "")

    # Auteurs
    authors = data.get("authors", {}).get("author", [])

    # Mots-clés
    keywords_list = data.get("authkeywords", {}).get("author-keyword", [])
    keywords = ", ".join(k.get("$", "") for k in keywords_list)

    # Sujets
    subject_list = data.get("subject-areas", {}).get("subject-area", [])
    subject_areas = ", ".join(s.get("$", "") for s in subject_list)

    return {
        "title": title,
        "abstract": abstract,
        "doi": doi,
        "journal_name": publication,
        "publication_year": year,
        "authors": authors,
        "keywords": keywords,
        "subject_areas": subject_areas,
        "scopus_id": scopus_id
    }

def extract_full_data(query):
    entries = search_scopus(query, max_results=100)
    full_data = []

    for entry in entries:
        scopus_identifier = entry.get("dc:identifier", "")
        if not scopus_identifier.startswith("SCOPUS_ID:"):
            continue

        scopus_id = scopus_identifier.split(":")[1]
        print(f"➡️ Détails pour {scopus_id}")
        details = get_article_details(scopus_id)

        if details:
            full_data.append(details)
        time.sleep(1)

    return full_data

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    query = "machine learning"

    print("⏳ Extraction en cours...")
    data = extract_full_data(query)

    with open("data/scopus_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Fichier 'scopus_data.json' généré avec abstracts, auteurs, mots-clés.")
