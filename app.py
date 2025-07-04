from flask import Flask, render_template, request, jsonify
from chatbot import ScopusChatbot
from search_engine import ScopusSearchEngine
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

app = Flask(__name__)
chatbot = ScopusChatbot()
search_engine = ScopusSearchEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('message', '')
        
        if not query:
            return jsonify({'error': 'Message vide'}), 400
        
        # Obtenir la réponse du chatbot
        response = chatbot.process_query(query)
        
        # Obtenir les résultats de recherche pour les visualisations
        results = search_engine.search(query, k=10)
        
        return jsonify({
            'response': response,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        k = data.get('k', 5)
        year_filter = data.get('year_filter', None)
        min_score = data.get('min_score', 0.0)
        
        results = search_engine.search(query, k=20)
        
        # Filtrer par année si spécifié
        if year_filter:
            results = [r for r in results if r.get('publication_year') == year_filter]
        
        # Filtrer par score minimum
        results = [r for r in results if r.get('similarity_score', 0) >= min_score]
        
        # Limiter aux k premiers résultats
        results = results[:k]
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    try:
        # Obtenir toutes les métadonnées pour l'analyse
        metadata = search_engine.metadata
        
        # Statistiques par année
        years_data = metadata['publication_year'].value_counts().sort_index()
        
        # Statistiques par journal
        journals_data = metadata['journal_name'].value_counts().head(10)
        
        # Graphique des publications par année
        fig_years = go.Figure()
        fig_years.add_trace(go.Scatter(
            x=years_data.index,
            y=years_data.values,
            mode='lines+markers',
            name='Publications par année',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=8)
        ))
        fig_years.update_layout(
            title='Évolution des Publications par Année',
            xaxis_title='Année',
            yaxis_title='Nombre de Publications',
            template='plotly_white'
        )
        
        # Graphique des journaux les plus populaires
        fig_journals = go.Figure()
        fig_journals.add_trace(go.Bar(
            x=journals_data.values,
            y=journals_data.index,
            orientation='h',
            marker=dict(color='#2196F3')
        ))
        fig_journals.update_layout(
            title='Top 10 des Journaux par Nombre de Publications',
            xaxis_title='Nombre de Publications',
            yaxis_title='Journal',
            template='plotly_white'
        )
        
        return jsonify({
            'years_chart': fig_years.to_json(),
            'journals_chart': fig_journals.to_json(),
            'total_articles': len(metadata),
            'unique_journals': metadata['journal_name'].nunique(),
            'year_range': f"{metadata['publication_year'].min()} - {metadata['publication_year'].max()}"
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/filters')
def get_filters():
    try:
        metadata = search_engine.metadata
        
        # Obtenir les années disponibles
        years = sorted(metadata['publication_year'].dropna().unique())
        
        # Obtenir les journaux disponibles
        journals = sorted(metadata['journal_name'].dropna().unique())
        
        return jsonify({
            'years': years,
            'journals': journals[:50]  # Limiter pour éviter une liste trop longue
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)