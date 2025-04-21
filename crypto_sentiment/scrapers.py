import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Cryptocurrency, SocialMediaPost
import logging
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Télécharger les ressources NLTK nécessaires
def download_nltk_resources():
    required_resources = [
        'punkt',
        'vader_lexicon',
        'stopwords',
        'punkt_tab',
        'averaged_perceptron_tagger',
        'wordnet'
    ]
    for resource in required_resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource)

# Télécharger les ressources au démarrage
download_nltk_resources()

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        
    def analyze_text(self, text):
        """Analyse le sentiment d'un texte et retourne un score entre 0 et 100"""
        # Nettoyer le texte
        tokens = word_tokenize(text.lower())
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in self.stop_words]
        cleaned_text = ' '.join(filtered_tokens)
        
        # Analyser le sentiment
        sentiment_scores = self.sia.polarity_scores(cleaned_text)
        
        # Convertir le score compound (-1 à 1) en score 0-100
        score = (sentiment_scores['compound'] + 1) * 50
        
        return score

class SocialMediaScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.sentiment_analyzer = SentimentAnalyzer()

    def scrape_reddit(self, crypto_symbol, subreddit='cryptocurrency'):
        """Scrape les posts Reddit concernant une cryptomonnaie"""
        try:
            url = f'https://www.reddit.com/r/{subreddit}/search.json?q={crypto_symbol}&restrict_sr=1&sort=new'
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                for post in data['data']['children']:
                    post_data = post['data']
                    # Combiner le titre et le contenu
                    content = f"{post_data['title']}\n\n{post_data['selftext']}"
                    created_at = timezone.make_aware(
                        datetime.fromtimestamp(post_data['created_utc']),
                        timezone.get_current_timezone()
                    )
                    
                    # Analyser le sentiment
                    sentiment_score = self.sentiment_analyzer.analyze_text(content)
                    
                    # Créer ou mettre à jour le post
                    SocialMediaPost.objects.update_or_create(
                        post_id=post_data['id'],
                        defaults={
                            'content': content,
                            'platform': 'REDDIT',
                            'created_at': created_at,
                            'sentiment_score': sentiment_score,
                            'cryptocurrency': Cryptocurrency.objects.get(symbol=crypto_symbol)
                        }
                    )
        except Exception as e:
            logger.error(f"Erreur lors du scraping Reddit pour {crypto_symbol}: {str(e)}")

    def scrape_4chan(self, crypto_symbol, board='biz'):
        """Scrape les threads 4chan concernant une cryptomonnaie"""
        try:
            url = f'https://boards.4channel.org/{board}/catalog'
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                threads = soup.find_all('div', class_='thread')
                
                for thread in threads:
                    if crypto_symbol.lower() in thread.text.lower():
                        thread_id = thread.get('id')
                        thread_url = f'https://boards.4channel.org/{board}/thread/{thread_id}'
                        
                        # Récupérer les posts du thread
                        thread_response = self.session.get(thread_url)
                        if thread_response.status_code == 200:
                            thread_soup = BeautifulSoup(thread_response.text, 'html.parser')
                            posts = thread_soup.find_all('div', class_='post')
                            
                            for post in posts:
                                content = post.find('div', class_='message').text
                                created_at = timezone.make_aware(
                                    datetime.fromtimestamp(int(post.get('data-time', 0))),
                                    timezone.get_current_timezone()
                                )
                                
                                # Analyser le sentiment
                                sentiment_score = self.sentiment_analyzer.analyze_text(content)
                                
                                SocialMediaPost.objects.update_or_create(
                                    post_id=f"4chan_{thread_id}_{post.get('data-no')}",
                                    defaults={
                                        'title': f"4chan Thread {thread_id}",
                                        'content': content,
                                        'platform': '4CHAN',
                                        'created_at': created_at,
                                        'sentiment_score': sentiment_score,
                                        'cryptocurrency': Cryptocurrency.objects.get(symbol=crypto_symbol)
                                    }
                                )
        except Exception as e:
            logger.error(f"Erreur lors du scraping 4chan pour {crypto_symbol}: {str(e)}")

    def scrape_telegram(self, crypto_symbol, channel):
        """Scrape les messages Telegram d'un canal spécifique"""
        try:
            # Note: Le scraping de Telegram nécessite une approche différente
            # car il utilise un protocole MTProto. Cette implémentation est un exemple
            # et nécessiterait l'utilisation de la bibliothèque Telethon ou Pyrogram
            pass
        except Exception as e:
            logger.error(f"Erreur lors du scraping Telegram pour {crypto_symbol}: {str(e)}")

    def run_scraping(self):
        """Exécute le scraping pour toutes les cryptomonnaies"""
        cryptocurrencies = Cryptocurrency.objects.all()
        for crypto in cryptocurrencies:
            logger.info(f"Début du scraping pour {crypto.symbol}")
            
            # Reddit
            self.scrape_reddit(crypto.symbol)
            time.sleep(2)  # Pause pour éviter d'être bloqué
            
            # 4chan
            self.scrape_4chan(crypto.symbol)
            time.sleep(2)
            
            # Telegram (à implémenter selon vos besoins)
            # self.scrape_telegram(crypto.symbol, 'channel_name')
            
            logger.info(f"Fin du scraping pour {crypto.symbol}") 