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
        # Utiliser les stop words français
        self.stop_words = set(stopwords.words('french'))
        
    def analyze_text(self, text):
        """Analyse le sentiment d'un texte et retourne un score entre 0 et 100"""
        # Nettoyer le texte
        tokens = word_tokenize(text.lower(), language='french')
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in self.stop_words]
        cleaned_text = ' '.join(filtered_tokens)
        
        # Analyser le sentiment avec adaptation pour le français
        sentiment_scores = self.sia.polarity_scores(cleaned_text)
        
        # Ajuster le score pour le français
        # On donne plus de poids aux mots positifs/négatifs français courants
        french_pos = {'bien', 'super', 'génial', 'excellent', 'parfait', 'incroyable', 'formidable'}
        french_neg = {'mauvais', 'nul', 'terrible', 'horrible', 'catastrophe', 'pire', 'médiocre'}
        
        words = set(cleaned_text.split())
        pos_count = sum(1 for word in words if word in french_pos)
        neg_count = sum(1 for word in words if word in french_neg)
        
        # Ajuster le score en fonction des mots français
        adjustment = (pos_count - neg_count) * 0.2
        score = (sentiment_scores['compound'] + 1 + adjustment) * 50
        
        # Garder le score entre 0 et 100
        return max(0, min(100, score))

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
            # Ajouter le filtre de langue française
            url = f'https://www.reddit.com/r/{subreddit}/search.json?q={crypto_symbol}+language%3Afr&restrict_sr=1&sort=new'
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
            # Utiliser l'API JSON de 4chan au lieu du HTML
            url = f'https://a.4cdn.org/{board}/catalog.json'
            response = self.session.get(url)
            if response.status_code == 200:
                threads_data = response.json()
                
                for page in threads_data:
                    for thread in page.get('threads', []):
                        # Vérifier si le thread parle de la crypto
                        thread_text = f"{thread.get('sub', '')} {thread.get('com', '')}"
                        if crypto_symbol.lower() in thread_text.lower():
                            thread_id = thread.get('no')
                            
                            # Récupérer les posts du thread via l'API
                            thread_url = f'https://a.4cdn.org/{board}/thread/{thread_id}.json'
                            thread_response = self.session.get(thread_url)
                            
                            if thread_response.status_code == 200:
                                thread_data = thread_response.json()
                                
                                for post in thread_data.get('posts', []):
                                    content = post.get('com', '')
                                    if not content:  # Ignorer les posts sans contenu
                                        continue
                                        
                                    # Nettoyer le HTML du contenu
                                    content = BeautifulSoup(content, 'html.parser').get_text()
                                    
                                    # Vérifier si le texte semble être en français
                                    if not any(word in content.lower() for word in ['le', 'la', 'les', 'un', 'une', 'des', 'est', 'sont']):
                                        continue
                                    
                                    created_at = timezone.make_aware(
                                        datetime.fromtimestamp(post.get('time', 0)),
                                        timezone.get_current_timezone()
                                    )
                                    
                                    # Analyser le sentiment
                                    sentiment_score = self.sentiment_analyzer.analyze_text(content)
                                    
                                    # Créer ou mettre à jour le post
                                    SocialMediaPost.objects.update_or_create(
                                        post_id=f"4chan_{thread_id}_{post.get('no')}",
                                        defaults={
                                            'content': content,
                                            'platform': '4CHAN',
                                            'created_at': created_at,
                                            'sentiment_score': sentiment_score,
                                            'cryptocurrency': Cryptocurrency.objects.get(symbol=crypto_symbol)
                                        }
                                    )
                            
                            # Attendre un peu pour éviter d'être bloqué
                            time.sleep(1)
                            
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

    def scrape_cryptofr(self, crypto_symbol):
        """Scrape les posts du forum CryptoFR"""
        try:
            # URL de base du forum CryptoFR
            base_url = 'https://cryptofr.com'
            search_url = f'{base_url}/search/search'
            
            # Paramètres de recherche
            params = {
                'keywords': crypto_symbol,
                'title_only': 1,
                'order': 'date',
                'direction': 'desc'
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                topics = soup.find_all('div', class_='structItem')
                
                for topic in topics:
                    title = topic.find('div', class_='structItem-title').text.strip()
                    content_preview = topic.find('div', class_='structItem-snippet').text.strip()
                    topic_id = topic.get('data-content')
                    
                    # Récupérer la date
                    date_element = topic.find('time')
                    if date_element and date_element.get('datetime'):
                        created_at = timezone.make_aware(
                            datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00')),
                            timezone.get_current_timezone()
                        )
                    else:
                        created_at = timezone.now()
                    
                    # Analyser le sentiment
                    content = f"{title}\n\n{content_preview}"
                    sentiment_score = self.sentiment_analyzer.analyze_text(content)
                    
                    # Créer ou mettre à jour le post
                    SocialMediaPost.objects.update_or_create(
                        post_id=f"cryptofr_{topic_id}",
                        defaults={
                            'content': content,
                            'platform': 'CRYPTOFR',
                            'created_at': created_at,
                            'sentiment_score': sentiment_score,
                            'cryptocurrency': Cryptocurrency.objects.get(symbol=crypto_symbol)
                        }
                    )
                    
                    # Attendre un peu pour éviter d'être bloqué
                    time.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"Erreur lors du scraping CryptoFR pour {crypto_symbol}: {str(e)}")
            
    def scrape_jvcom(self, crypto_symbol):
        """Scrape les posts du forum JVC Cryptomonnaies"""
        try:
            # URL de base du forum JVC
            forum_url = 'https://www.jeuxvideo.com/forums/42-3011927-0-1-0-1-0-crypto-monnaies.htm'
            
            response = self.session.get(forum_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                topics = soup.find_all('li', class_='topic')
                
                for topic in topics:
                    if crypto_symbol.lower() in topic.text.lower():
                        title = topic.find('a', class_='topic-title').text.strip()
                        topic_id = topic.get('data-id')
                        topic_url = f"https://www.jeuxvideo.com/forums/message/{topic_id}"
                        
                        # Récupérer le contenu du topic
                        topic_response = self.session.get(topic_url)
                        if topic_response.status_code == 200:
                            topic_soup = BeautifulSoup(topic_response.text, 'html.parser')
                            first_post = topic_soup.find('div', class_='txt-msg')
                            if first_post:
                                content = f"{title}\n\n{first_post.text.strip()}"
                                
                                # Récupérer la date
                                date_element = topic.find('span', class_='topic-date')
                                if date_element:
                                    date_str = date_element['title']
                                    try:
                                        created_at = timezone.make_aware(
                                            datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S'),
                                            timezone.get_current_timezone()
                                        )
                                    except:
                                        created_at = timezone.now()
                                else:
                                    created_at = timezone.now()
                                
                                # Analyser le sentiment
                                sentiment_score = self.sentiment_analyzer.analyze_text(content)
                                
                                # Créer ou mettre à jour le post
                                SocialMediaPost.objects.update_or_create(
                                    post_id=f"jvcom_{topic_id}",
                                    defaults={
                                        'content': content,
                                        'platform': 'JVCOM',
                                        'created_at': created_at,
                                        'sentiment_score': sentiment_score,
                                        'cryptocurrency': Cryptocurrency.objects.get(symbol=crypto_symbol)
                                    }
                                )
                        
                        # Attendre un peu pour éviter d'être bloqué
                        time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Erreur lors du scraping JVC pour {crypto_symbol}: {str(e)}")

    def run_scraping(self):
        """Exécute le scraping pour toutes les cryptomonnaies"""
        cryptocurrencies = Cryptocurrency.objects.all()
        
        for crypto in cryptocurrencies:
            logger.info(f"Début du scraping pour {crypto.symbol}")
            
            # Scraping Reddit
            self.scrape_reddit(crypto.symbol)
            
            # Scraping CryptoFR
            self.scrape_cryptofr(crypto.symbol)
            
            # Scraping JVC
            self.scrape_jvcom(crypto.symbol)
            
            logger.info(f"Fin du scraping pour {crypto.symbol}")