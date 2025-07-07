import os
import requests
import json
import time
import feedparser

# Chemin où enregistrer les données
DATA_PATH = "data/my_data.json"

def search_arxiv(query, max_results=100):
    """
    Recherche d'articles Arxiv par requête.
    """
    results = []
    start = 0
    count_per_page = 25

    while start < max_results:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f'all:"{query}"',
            "start": start,
            "max_results": count_per_page
        }

        print(f"🔎 Extraction {start} à {start + count_per_page}...")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            if not feed.entries:
                print("✅ Aucun autre résultat, extraction terminée.")
                break

            for entry in feed.entries:
                authors = [author.name for author in entry.authors]

                article = {
                    "title": entry.title,
                    "abstract": entry.summary,
                    "doi": "",  # Pas toujours dispo dans Arxiv
                    "journal_name": "Arxiv",
                    "publication_year": entry.published.split("T")[0],
                    "authors": authors,
                    "keywords": "",  # Non disponible
                    "subject_areas": "",  # Non disponible
                    "scopus_id": entry.id  # On garde l'ID Arxiv comme identifiant
                }

                results.append(article)

            start += count_per_page
            time.sleep(1)  # Politesse

        except Exception as e:
            print(f"❌ Erreur : {e}")
            break

    return results


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    query = "machine learning"  # Modifie ta requête ici

    print("⏳ Extraction en cours avec Arxiv...")
    data = search_arxiv(query, max_results=100)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Extraction terminée. {len(data)} articles enregistrés dans '{DATA_PATH}'")
