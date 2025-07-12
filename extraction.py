import os
import json
import time
import feedparser
import requests

# 📁 Dossier de sauvegarde
DATA_PATH = "data/arxiv_data.json"
os.makedirs("data", exist_ok=True)

# 🔍 Liste des domaines à rechercher
QUERIES = [
    "machine learning",
    "deep learning",
    "medical imaging",
    "mathematics",
    "artificial intelligence",
    "healthcare",
    "data science"
]

def search_arxiv(query, max_results=100):
    articles = []
    base_url = "http://export.arxiv.org/api/query"
    start = 0
    count_per_page = 100

    while start < max_results:
        params = {
            "search_query": f'all:"{query}"',
            "start": start,
            "max_results": count_per_page
        }

        print(f"🔎 Extraction : {query} (résultats {start + 1} à {start + count_per_page})")

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            if not feed.entries:
                break

            for entry in feed.entries:
                title = entry.title.strip().replace("\n", " ")
                summary = entry.summary.strip().replace("\n", " ")
                published = entry.published[:10] if 'published' in entry else ""
                publication_year = published[:4] if published else None
                authors = [author.name for author in entry.authors] if 'authors' in entry else []
                categories = [tag['term'] for tag in entry.tags] if 'tags' in entry else []
                article_id = entry.id

                # 📎 Lien PDF
                pdf_url = None
                for link in entry.links:
                    if link.type == "application/pdf":
                        pdf_url = link.href
                        break

                article = {
                    "title": title,
                    "abstract": summary,
                    "publication_year": publication_year,
                    "journal_name": "ArXiv",
                    "doi": None,
                    "scopus_identifier": article_id,
                    "keywords": ", ".join(categories),
                    "subject_areas": ", ".join(categories),
                    "authors": authors,
                    "pdf_url": pdf_url
                }

                articles.append(article)

            start += count_per_page
            time.sleep(1)

        except Exception as e:
            print(f"❌ Erreur pour '{query}': {e}")
            break

    return articles

if __name__ == "__main__":
    all_articles = []

    for query in QUERIES:
        extracted = search_arxiv(query, max_results=100)
        all_articles.extend(extracted)

    # ✅ Supprimer les doublons (par ID arXiv)
    seen_ids = set()
    unique_articles = []
    for art in all_articles:
        if art["scopus_identifier"] not in seen_ids:
            unique_articles.append(art)
            seen_ids.add(art["scopus_identifier"])

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(unique_articles, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Total final : {len(unique_articles)} articles enregistrés dans '{DATA_PATH}'")
