import os
import json
import feedparser
import urllib.parse  # ✅ Import pour encoder l’URL

os.makedirs("data", exist_ok=True)

def extract_full_data(query="machine learning", max_results=250):
    print(f"🔍 Lancement de l'extraction ArXiv pour : '{query}'...")

    base_url = "http://export.arxiv.org/api/query?"
    query_encoded = urllib.parse.quote(query)  # ✅ Encodage correct
    search_query = f"search_query=all:{query_encoded}&start=0&max_results={max_results}"
    url = base_url + search_query

    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries:
        title = entry.title.strip().replace("\n", " ")
        summary = entry.summary.strip().replace("\n", " ")
        published = entry.published[:10]
        authors = [author.name for author in entry.authors]
        categories = [tag['term'] for tag in entry.tags]
        article_id = entry.id

        article = {
            "title": title,
            "abstract": summary,
            "publication_year": published[:4],
            "journal_name": "ArXiv",
            "doi": None,
            "scopus_identifier": article_id,
            "keywords": ", ".join(categories),
            "subject_areas": ", ".join(categories),
            "authors": [{"full_name": a, "scopus_author_id": None, "orcid": None,
                         "main_affiliation_id": None,
                         "affiliation": {"affiliation_id": None, "name": None, "country": None}} for a in authors]
        }

        articles.append(article)

    with open("data/arxiv_full_data.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    print(f"✅ {len(articles)} articles sauvegardés dans data/arxiv_full_data.json")

if __name__ == "__main__":
    extract_full_data("machine learning")
