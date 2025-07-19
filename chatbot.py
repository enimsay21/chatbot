from search_engine import ScopusSearchEngine

class ScopusChatbot:
    def __init__(self):
        self.search_engine = ScopusSearchEngine()

    def process_query(self, query: str) -> str:
        if not query.strip():
            return "Veuillez saisir une question valide."

        # Appel avec le seuil de similarité explicite
        results = self.search_engine.search(query, k=5)

        if not results:
            return "Désolé, aucun article correspondant n'a été trouvé."

        response = f"Voici les {len(results)} articles les plus pertinents que j'ai trouvés :\n\n"
        for i, article in enumerate(results, 1):
            response += (
                f"{i}. {article['title']}\n"
                f"Auteurs: {article['authors']}\n"
                f"Résumé: {article['abstract']}\n"
                f"Année: {article['publication_year']}\n"
                f"Score de similarité: {article['similarity_score']:.2f}\n"
            )
            if article.get("pdf_url"):
                response += f"🔗 PDF: {article['pdf_url']}\n"
            response += "\n"

        return response
