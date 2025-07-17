# Winalyze - League of Legends Stats Dashboard

Winalyze est une application web de data visualisation permettant d’analyser les performances d’un joueur sur **League of Legends**, via l’API officielle de Riot Games.

## 📊 Fonctionnalités

- 🎯 Visualisation des statistiques par semaine, mois et jour
- 🧠 Graphiques interactifs (radar, camembert, barres)
- 🔍 Suivi de l’évolution du rang, des comptes utilisés et des performances
- 🛠️ Interface simple développée avec Dash et Plotly

## 🧱 Technologies utilisées

- Python
- Dash (Plotly)
- Pandas
- Riot API
- dotenv
- Requests

## 📦 Installation

1. Clone le dépôt :

   ```bash
   git clone https://github.com/xentee/dataviz-winalyze.git
   cd dataviz-winalyze
   ```

2. (Optionnel) Crée un environnement virtuel :

   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. Installe les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

4. Crée un fichier `.env` avec ta clé API Riot :

   ```env
   RIOT_API_KEY=ta_cle_riot_ici
   ```

5. Lance l’application :

   ```bash
   python app.py
   ```

6. Accède à l’interface via [http://localhost:8050](http://localhost:8050)
