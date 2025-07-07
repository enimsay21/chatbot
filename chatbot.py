import json
import os
import re
from datetime import datetime
import collections
from search_engine import ScopusSearchEngine  # Assure-toi que ce module existe

class ScopusChatbot:
    def __init__(self):
        self.search_engine = ScopusSearchEngine()
        self.greetings = ["bonjour", "salut", "hello", "hi", "bonsoir"]
        self.goodbyes = ["au revoir", "bye", "goodbye", "à plus", "à bientôt"]
        self.thanks = ["merci", "thanks", "thank you"]
        
    def process_query(self, query):
        query = query.strip()
        lower_query = query.lower()
        
        if any(greet in lower_query for greet in self.greetings):
            return {'type': 'greeting', 'message': "👋 Bonjour! Comment puis-je vous aider aujourd'hui?"}
        
        if any(thank in lower_query for thank in self.thanks):
            return {'type': 'thanks', 'message': "😊 Je vous en prie! N'hésitez pas si vous avez d'autres questions."}
        
        if any(bye in lower_query for bye in self.goodbyes):
            return {'type': 'goodbye', 'message': "👋 Au revoir! À bientôt!"}
        
        try:
            results = self.search_engine.search(query, k=10)
            if not results:
                return {'type': 'no_results', 'message': "❌ Aucun résultat trouvé."}
            
            analysis = self.analyze_results(results)
            response = self.format_response(results, analysis, query)
            
            return {
                'type': 'search_results',
                'message': response,
                'results': results[:5],
                'analysis': analysis
            }
        except Exception as e:
            return {'type': 'error', 'message': f"❌ Erreur: {str(e)}"}
    
    def analyze_results(self, results):
        years = []
        journals = []
        scores = []
        
        for r in results:
            y = r.get('publication_year')
            if isinstance(y, int):
                years.append(y)
            elif isinstance(y, str) and y.isdigit():
                years.append(int(y))
            journal = r.get('journal_name')
            if journal:
                journals.append(journal)
            scores.append(r.get('similarity_score', 0))
        
        year_analysis = {
            'min_year': min(years) if years else None,
            'max_year': max(years) if years else None,
            'avg_year': sum(years) / len(years) if years else None
        }
        
        journal_counts = collections.Counter(journals)
        
        score_analysis = {
            'avg_similarity': sum(scores) / len(scores) if scores else 0,
            'best_match': max(scores) if scores else 0,
            'high_relevance_count': len([s for s in scores if s > 0.7])
        }
        
        return {
            'total_results': len(results),
            'year_analysis': year_analysis,
            'top_journals': journal_counts.most_common(3),
            'score_analysis': score_analysis
        }
    
    def format_response(self, results, analysis, query):
        total = analysis['total_results']
        avg_similarity = analysis['score_analysis']['avg_similarity']
        
        if avg_similarity > 0.8:
            intro = f"🎯 {total} publications très pertinentes trouvées."
        elif avg_similarity > 0.6:
            intro = f"📚 {total} publications pertinentes trouvées."
        else:
            intro = f"🔍 {total} publications trouvées."
        
        year_info = ""
        if analysis['year_analysis']['min_year'] and analysis['year_analysis']['max_year']:
            min_year = analysis['year_analysis']['min_year']
            max_year = analysis['year_analysis']['max_year']
            year_info = f" De {min_year} à {max_year}."
        
        journal_info = ""
        if analysis['top_journals']:
            journal_info = f" Journal le plus fréquent: {analysis['top_journals'][0][0]}."
        
        response = f"{intro}{year_info}{journal_info}\n\n📑 Publications clés:\n"
        for i, r in enumerate(results[:3], 1):
            title = r.get('title', 'Titre inconnu')
            year = r.get('publication_year', 'Année inconnue')
            journal = r.get('journal_name', 'Journal inconnu')
            sim = r.get('similarity_score', 0)
            response += f"{i}. **{title}** ({year})\n   📚 {journal}\n   ⭐ Pertinence: {sim:.1%}\n\n"
        
        return response

