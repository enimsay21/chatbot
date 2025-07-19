**Chatbot de Recherche Scientifique**
Ce projet propose un chatbot intelligent permettant de faciliter la recherche d’articles scientifiques grâce aux technologies NLP, FAISS. Il intègre une interface simple  pour interagir naturellement avec une base de données scientifique.

**Fonctionnalités**
- Recherche d’articles via une question ou mot-clé
- Résumés automatiques d’articles (via NLP)
- Base ArXiv intégrée 
- Réponses contextualisées avec embeddings (FAISS)
- Interface utilisateur (Streamlit )
- Visualisation interactive (Plotly)

**Installation**
1. Cloner le projet :
"bash":
git clone https://github.com/enimsay21/chatbot.git
cd chatbot
2. Installer les dépendances :
pip install --upgrade pip
pip install -r requirements.txt
->Manipulation de données :
pip install pandas numpy
->Traitement du langage naturel (NLP) :
pip install transformers sentence-transformers
->Recherche vectorielle (semantic search) :
pip install faiss-cpu
->Visualisation de données :
pip install matplotlib plotly
->Interfaces web :
pip install streamlit

**Lancement**
En interface Web avec Streamlit
->streamlit run app.py

**Comment utliser le chatbot (interfaces utilisateurs)**
1. Interface de question-réponse (Q&A)
- Permet à l’utilisateur de poser une question libre au chatbot.
- Le chatbot renvoie une réponse structurée avec :
Titre de l'article le plus pertinent
Résumé synthétique
Auteur(s) de la publication
Le lien pdf d'article
L'année de publication

2. Interface de visualisation de données
Affiche des graphiques interactifs via Plotly :
- le nuage de mots 
- Les auteurs les plus publiants
- La répartition des publications par année

Ces diagrammes permettent de comprendre rapidement les tendances scientifiques dans la base analysée.

3. Interface de recherche sémantique avec filtres
    L’utilisateur peut effectuer une recherche rapide par mot-clé.
    Résultats obtenus grâce à un moteur de recherche sémantique (FAISS + embeddings).
    Possibilité d’appliquer des filtres dynamiques :
      - Par année de publication
      - Par nom d’auteur
      - Par mots-clés
**Contributeurs**
CHAHMI Nouhaila, FKIKIH Yasmine :Développeurs principaux
MADANI Abdellah:Encadrant
