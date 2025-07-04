from search_engine import ScopusSearchEngine
import re
import json
from datetime import datetime

class ScopusChatbot:
    def __init__(self):
        self.search_engine = ScopusSearchEngine()
        self.greetings = ["bonjour", "salut", "hello", "hi", "bonsoir"]
        self.goodbyes = ["au revoir", "bye", "goodbye", "à plus", "à bientôt"]
        self.thanks = ["merci", "thanks", "thank you"]
        
    def process_query(self, query):
        """Traite une requête et retourne une réponse formatée"""
        # Nettoyer la requête
        query = query.strip()
        
        # Vérifier les salutations
        if any(greet in query.lower() for greet in self.greetings):
            return {
                'type': 'greeting',
                'message': "👋 Bonjour! Je suis votre assistant de recherche Scopus spécialisé dans les publications scientifiques. Comment puis-je vous aider aujourd'hui?"
            }
        
        # Vérifier les remerciements
        if any(thank in query.lower() for thank in self.thanks):
            return {
                'type': 'thanks',
                'message': "😊 Je vous en prie! N'hésitez pas si vous avez d'autres questions sur les publications scientifiques."
            }
        
        # Vérifier les au revoirs
        if any(gbye in query.lower() for gbye in self.goodbyes):
            return {
                'type': 'goodbye',
                'message': "👋 Au revoir! J'espère avoir pu vous aider dans vos recherches. À bientôt!"
            }
        
        # Effectuer la recherche sémantique
        try:
            results = self.search_engine.search(query, k=10)
            
            if not results:
                return {
                    'type': 'no_results',
                    'message': "❌ Je n'ai trouvé aucune publication correspondant à votre requête. Essayez avec d'autres mots-clés ou des termes plus généraux."
                }
            
            # Analyser les résultats
            analysis = self.analyze_results(results, query)
            
            # Formater la réponse
            response = self.format_response(results, analysis, query)
            
            return {
                'type': 'search_results',
                'message': response,
                'results': results[:5],  # Limiter à 5 résultats pour le chat
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'message': f"❌ Une erreur s'est produite lors de la recherche: {str(e)}"
            }
    
    def analyze_results(self, results, query):
        """Analyse les résultats pour fournir des insights"""
        if not results:
            return {}
        
        # Analyser les années
        years = [r.get('publication_year') for r in results if r.get('publication_year')]
        year_analysis = {
            'min_year': min(years) if years else None,
            'max_year': max(years) if years else None,
            'avg_year': sum(years) / len(years) if years else None
        }
        
        # Analyser les journaux
        journals = [r.get('journal_name') for r in results if r.get('journal_name')]
        journal_counts = {}
        for journal in journals:
            journal_counts[journal] = journal_counts.get(journal, 0) + 1
        
        # Analyser les scores de similarité
        scores = [r.get('similarity_score', 0) for r in results]
        score_analysis = {
            'avg_similarity': sum(scores) / len(scores) if scores else 0,
            'best_match': max(scores) if scores else 0,
            'high_relevance_count': len([s for s in scores if s > 0.7])
        }
        
        return {
            'total_results': len(results),
            'year_analysis': year_analysis,
            'top_journals': sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            'score_analysis': score_analysis
        }
    
    def format_response(self, results, analysis, query):
        """Formate une réponse conversationnelle"""
        total = analysis['total_results']
        avg_similarity = analysis['score_analysis']['avg_similarity']
        
        # Introduction
        if avg_similarity > 0.8:
            intro = f"🎯 Excellente nouvelle! J'ai trouvé {total} publications très pertinentes pour votre recherche."
        elif avg_similarity > 0.6:
            intro = f"📚 J'ai trouvé {total} publications relativement pertinentes pour votre requête."
        else:
            intro = f"🔍 J'ai trouvé {total} publications qui pourraient vous intéresser, bien que la correspondance soit modérée."
        
        # Analyse temporelle
        year_info = ""
        if analysis['year_analysis']['min_year'] and analysis['year_analysis']['max_year']:
            min_year = analysis['year_analysis']['min_year']
            max_year = analysis['year_analysis']['max_year']
            
            if min_year == max_year:
                year_info = f" Les publications datent principalement de {min_year}."
            else:
                year_info = f" Les publications s'étendent de {min_year} à {max_year}."
        
        # Analyse des journaux
        journal_info = ""
        if analysis['top_journals']:
            top_journal = analysis['top_journals'][0][0]
            journal_info = f" Le journal le plus représenté est '{top_journal}'."
        
        # Recommandations
        recommendations = self.generate_recommendations(results, query)
        
        # Construire la réponse finale
        response = f"{intro}{year_info}{journal_info}\n\n"
        
        if recommendations:
            response += f"💡 {recommendations}\n\n"
        
        response += "📑 Voici les publications les plus pertinentes:\n\n"
        
        # Ajouter les top 3 résultats
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', 'Titre non disponible')
            year = result.get('publication_year', 'Année inconnue')
            journal = result.get('journal_name', 'Journal inconnu')
            similarity = result.get('similarity_score', 0)
            
            response += f"{i}. **{title}** ({year})\n"
            response += f"   📚 {journal}\n"
            response += f"   ⭐ Pertinence: {similarity:.1%}\n\n"
        
        if len(results) > 3:
            response += f"... et {len(results) - 3} autres publications disponibles dans les résultats détaillés."
        
        return response
    
    def generate_recommendations(self, results, query):
        """Génère des recommandations basées sur les résultats"""
        if not results:
            return ""
        
        avg_similarity = sum(r.get('similarity_score', 0) for r in results) / len(results)
        
        if avg_similarity < 0.5:
            return "Vous pourriez obtenir de meilleurs résultats en reformulant votre question avec des termes plus spécifiques."
        
        # Analyser les mots-clés manquants
        years = [r.get('publication_year') for r in results if r.get('publication_year')]
        if years:
            recent_count = len([y for y in years if y >= 2020])
            if recent_count < len(years) * 0.3:
                return "La plupart des publications trouvées sont antérieures à 2020. Essayez d'ajouter 'recent' ou '2020-2024' à votre recherche pour des travaux plus récents."
        
        return "Les résultats semblent très pertinents pour votre recherche!"
    
    def get_stats(self):
        """Retourne des statistiques sur la base de données"""
        try:
            total_articles = len(self.search_engine.metadata)
            
            # Analyser les années
            years = [item.get('publication_year') for item in self.search_engine.metadata if item.get('publication_year')]
            year_range = f"{min(years)} - {max(years)}" if years else "Non disponible"
            
            # Analyser les journaux
            journals = set([item.get('journal_name') for item in self.search_engine.metadata if item.get('journal_name')])
            
            return {
                'total_articles': total_articles,
                'year_range': year_range,
                'unique_journals': len(journals),
                'database_status': 'Opérationnel'
            }
        except Exception as e:
            return {
                'total_articles': 0,
                'year_range': 'Erreur',
                'unique_journals': 0,
                'database_status': f'Erreur: {str(e)}'
            }
    
    def suggest_related_queries(self, query, results):
        """Suggère des requêtes connexes basées sur les résultats"""
        if not results:
            return []
        
        suggestions = []
        
        # Extraire les journaux populaires
        journals = [r.get('journal_name') for r in results if r.get('journal_name')]
        if journals:
            top_journal = max(set(journals), key=journals.count)
            suggestions.append(f"Publications dans {top_journal}")
        
        # Suggérer des recherches par période
        years = [r.get('publication_year') for r in results if r.get('publication_year')]
        if years:
            recent_years = [y for y in years if y >= 2020]
            if recent_years:
                suggestions.append(f"Recherches récentes sur {query.lower()}")
        
        # Suggérer des termes connexes basés sur les titres
        common_words = self.extract_common_terms(results)
        if common_words:
            suggestions.append(f"{query} + {common_words[0]}")
        
        return suggestions[:3]  # Limiter à 3 suggestions
    
    def extract_common_terms(self, results):
        """Extrait les termes communs des titres"""
        import collections
        
        all_words = []
        for result in results:
            title = result.get('title', '')
            # Nettoyer et extraire les mots
            words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
            all_words.extend(words)
        
        # Mots à ignorer
        stop_words = {'with', 'from', 'this', 'that', 'have', 'been', 'were', 'are', 'and', 'the', 'for', 'analysis', 'study', 'research'}
        
        filtered_words = [w for w in all_words if w not in stop_words]
        
        if not filtered_words:
            return []
        
        # Retourner les mots les plus fréquents
        word_counts = collections.Counter(filtered_words)
        return [word for word, count in word_counts.most_common(5) if count > 1]