import tweepy
import os
from datetime import datetime, timedelta
from textblob import TextBlob
from django.conf import settings
from dotenv import load_dotenv
from ..models import Cryptocurrency, SocialMediaPost

load_dotenv()

class TwitterService:
    def __init__(self):
        # Utilisation de l'API v2
        self.client = tweepy.Client(
            bearer_token=None,  # Nous utilisons l'authentification OAuth 1.0a
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )

    def analyze_sentiment(self, text):
        analysis = TextBlob(text)
        # Convertir la polarité (-1 à 1) en pourcentage (0 à 100)
        return (analysis.sentiment.polarity + 1) * 50

    def collect_tweets(self, cryptocurrency):
        """
        Collecte les tweets récents concernant une cryptomonnaie
        """
        query = f"#{cryptocurrency.symbol} OR ${cryptocurrency.symbol} -is:retweet lang:fr"
        
        try:
            # Utilisation de l'API v2 pour rechercher des tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'text']
            )
            
            if not tweets.data:
                print(f"Aucun tweet trouvé pour {cryptocurrency.symbol}")
                return
                
            for tweet in tweets.data:
                # Vérifier si le tweet existe déjà
                if not SocialMediaPost.objects.filter(post_id=str(tweet.id)).exists():
                    sentiment_score = self.analyze_sentiment(tweet.text)
                    
                    SocialMediaPost.objects.create(
                        cryptocurrency=cryptocurrency,
                        platform='TWITTER',
                        post_id=str(tweet.id),
                        content=tweet.text,
                        sentiment_score=sentiment_score,
                        created_at=tweet.created_at
                    )
                    print(f"Tweet ajouté pour {cryptocurrency.symbol}: {tweet.text[:50]}...")
        except Exception as e:
            print(f"Erreur lors de la collecte des tweets pour {cryptocurrency.symbol}: {str(e)}")

    def update_all_cryptocurrencies(self):
        """
        Met à jour les données pour toutes les cryptomonnaies
        """
        cryptocurrencies = Cryptocurrency.objects.all()
        for crypto in cryptocurrencies:
            try:
                self.collect_tweets(crypto)
            except Exception as e:
                print(f"Erreur lors de la collecte des tweets pour {crypto.symbol}: {str(e)}") 