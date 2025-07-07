import json
import os
from semantic_index import SemanticSearch

# Charger les données extraites
with open("data/my_data.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

# Initialiser l'index sémantique
search_engine = SemanticSearch(articles)

def answer_question(question):
    """
    Prend une question en entrée et retourne la réponse la plus pertinente.
    """
    result = search_engine.search(question, top_n=1)

    if not result:
        return "❌ Désolé, je n'ai pas trouvé de réponse pertinente."

    best_article = result[0]
    title = best_article.get("title", "Titre inconnu")
    abstract = best_article.get("abstract", "Pas de résumé disponible.")
    doi = best_article.get("doi", "DOI inconnu")

    return f"📄 **Titre** : {title}\n📝 **Résumé** : {abstract}\n🔗 **DOI** : {doi}"
