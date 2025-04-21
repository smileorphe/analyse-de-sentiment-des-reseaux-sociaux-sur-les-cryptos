# Crypto Sentiment Analyzer ![Django](https://img.shields.io/badge/Django-5.2-green) ![Tests](https://img.shields.io/badge/tests-passing-brightgreen) ![Licence](https://img.shields.io/badge/license-MIT-blue)

---

## 1. Titre du Projet

**Crypto Sentiment Analyzer**

_(Icône/logo à insérer ici)_

---

## 2. Description

Outil d'analyse de sentiment autour des cryptomonnaies à partir de sources web variées.

**Fonctionnalités principales :**
- Scraping de forums (Reddit, 4chan, etc.)
- Analyse de sentiment automatisée
- Tableau de bord de consultation
- Planification de tâches avec Celery
- Stockage des résultats en base de données

---

## 3. Prérequis Techniques

- **Python** : >= 3.10
- **Django** : >= 5.2
- **Packages critiques** :
  - requests >= 2.31.0
  - beautifulsoup4 >= 4.12.0
  - textblob >= 0.17.1
  - python-dateutil >= 2.8.2
  - celery >= 5.3.0
  - redis >= 5.0.0
- **Base de données** : SQLite par défaut (support PostgreSQL/MySQL possible)

---

## 4. Installation

```bash
git clone [lien-du-projet]
cd Sentiment2
python -m venv venv
# Sous Linux/macOS	source venv/bin/activate
# Sous Windows	venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

---

## 5. Configuration

Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```env
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

---

## 6. Lancement

```bash
python manage.py runserver
```

---

## 7. Tests

```bash
python manage.py test
```

---

## 8. Structure du Projet

```
/Sentiment2/
  ├── /crypto_sentiment/   # Application principale
  ├── /static/             # Fichiers statiques
  ├── manage.py            # Script de gestion
  └── settings.py          # Configuration (dans /crypto_sentiment/)
```

---

## 9. Déploiement

- **Heroku** :
  - Ajouter Procfile, requirements.txt et runtime.txt
  - Configurer les variables d'environnement
- **Docker** :
  - Fournir un `Dockerfile` et un fichier `docker-compose.yml`
  - Exposer les ports nécessaires

---

## 10. Contribution

- Forker le projet
- Créer une branche pour vos modifications
- Soumettre une Pull Request
- Ouvrir des issues pour signaler des bugs ou proposer des améliorations

---

## 11. Licence

Ce projet est sous licence MIT.

---

## Bonus

- **Badges** : Statut CI, couverture de tests, version Django (voir en haut du fichier)
- **Captures d'écran** : _(À insérer ici si interface graphique)_

---

> _Merci de contribuer à Crypto Sentiment Analyzer !_
