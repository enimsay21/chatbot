**Chatbot de Recherche Scientifique**
Ce projet propose un chatbot intelligent permettant de faciliter la recherche d’articles scientifiques grâce aux technologies NLP, 
LangChain, FAISS. Il intègre une interface simple (CLI/Web/Streamlit) pour interagir naturellement avec une base de données scientifique.

**Table des matières**
- [ Fonctionnalités]
- [ Technologies]
- [ Structure du projet]
- [ Installation]
- [ Lancement]
- [ Exemple d'utilisation]
- [ Perspectives]
- [ Contributeurs]
- [ Licence]

**Fonctionnalités**
- Recherche d’articles via une question ou mot-clé
- Résumés automatiques d’articles (via NLP)
- Base ArXiv intégrée (fichier local ou API)
- Réponses contextualisées avec embeddings (FAISS)
- Interface utilisateur (Streamlit ou Flask)
- Visualisation interactive (Plotly)

**Structure du projet**
chatbot_project/
├── data/ #Fichiers ArXiv nettoyés#
├── models/  Modèles NLP, embeddings
├── app/  #Interface Streamlit#
├── Extraction 
    nettoyage
├── research_engine.py
    semantic_index.py
├── requirements.txt # Dépendances du projet#
└── README.md # Ce fichier

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

**Exemple d'utilisation**
> Quelle est la dernière publication sur les transformers ?
Réponse : "Title: Recent Advances in Transformers" (2023), par A. Smith...

**Perspectives**
->Intégrer d'autres bases (Scopus, PubMed)

->Ajouter des LLM open-source (LLAMA, Mistral)

->Système de filtres personnalisés (année, domaine)

->Déploiement sur HuggingFace, Render ou Streamlit Cloud

**Contributeurs**
CHAHMI Nouhaila, FKIKIH Yasmine :Développeurs principaux
MADANI Abdellah:Encadrant
