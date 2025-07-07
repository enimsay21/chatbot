import os
import json
import time
import feedparser
import urllib.parse
import requests

# Chemin du dossier de sauvegarde
DATA_PATH = "data/arxiv_data.json"
os.makedirs("data", exist_ok=True)

def search_arxiv(query="machine learning", max_results=100):
    """
    Recherche et extrait des articles depuis ArXiv en fonction d'une requête donnée.
    Enregistre les résultats au format JSON.
    """
    articles = []
    base_url = "http://export.arxiv.org/api/query"
    start = 0
    count_per_page = 25

    while start < max_results:
        # Encodage correct de la requête pour l'URL
        params = {
            "search_query": f'all:"{query}"',
            "start": start,
            "max_results": count_per_page
        }

        print(f"🔎 Extraction des résultats {start + 1} à {start + count_per_page}...")

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if not feed.entries:
                print("✅ Aucun autre résultat, extraction terminée.")
                break

            for entry in feed.entries:
                title = entry.title.strip().replace("\n", " ")
                summary = entry.summary.strip().replace("\n", " ")
                published = entry.published[:10] if 'published' in entry else ""
                publication_year = published[:4] if published else None
                authors = [author.name for author in entry.authors] if 'authors' in entry else []
                categories = [tag['term'] for tag in entry.tags] if 'tags' in entry else []
                article_id = entry.id

                article = {
                    "title": title,
                    "abstract": summary,
                    "publication_year": publication_year,
                    "journal_name": "ArXiv",
                    "doi": None,
                    "scopus_identifier": article_id,
                    "keywords": ", ".join(categories),
                    "subject_areas": ", ".join(categories),
                    "authors": authors  # Simple liste d'auteurs
                }

                articles.append(article)

            start += count_per_page
            time.sleep(1)  # Pause entre les requêtes pour respecter les bonnes pratiques

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des articles : {e}")
            break

    return articles

if __name__ == "__main__":
    query = "machine learning"  # 👉 Tu peux changer la requête ici
    max_results = 100

    print(f"⏳ Lancement de l'extraction ArXiv pour '{query}'...")
    extracted_articles = search_arxiv(query, max_results=max_results)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted_articles, f, ensure_ascii=False, indent=4)

    print(f"✅ Extraction terminée : {len(extracted_articles)} articles sauvegardés dans '{DATA_PATH}'.")
