**Chatbot de Recherche Scientifique**
Ce projet propose un chatbot intelligent permettant de faciliter la recherche d’articles scientifiques grâce aux technologies NLP, FAISS. Il intègre une interface simple  pour interagir naturellement avec une base de données scientifique.



**Fonctionnalités**
- Recherche d’articles via une question ou mot-clé
- Résumés automatiques d’articles (via NLP)
- Base ArXiv intégrée (fichier local ou API)
- Réponses contextualisées avec embeddings (FAISS)
- Interface utilisateur (Streamlit ou Flask)
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
pip install nltk spacy transformers sentence-transformers
->Recherche vectorielle (semantic search) :
pip install faiss-cpu
->Visualisation de données :
pip install matplotlib plotly
->Interfaces web :
pip install streamlit

**Lancement**
En interface Web avec Streamlit
->streamlit run app/streamlit_app.py

..**Comment utliser le chatbot par utlisateur**



**Contributeurs**
CHAHMI Nouhaila, FKIKIH Yasmine :Développeurs principaux
MADANI Abdellah:Encadrant
