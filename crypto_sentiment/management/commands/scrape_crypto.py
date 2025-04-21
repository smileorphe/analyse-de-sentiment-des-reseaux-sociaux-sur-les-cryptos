from django.core.management.base import BaseCommand
from crypto_sentiment.models import Cryptocurrency, SocialMediaPost, SentimentAnalysis
from crypto_sentiment.scrapers import SocialMediaScraper, SentimentAnalyzer
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count
import random

class Command(BaseCommand):
    help = 'Scrape cryptocurrency sentiment data from various sources'

    def calculate_sentiment_scores(self, text, base_score):
        """Calcule les scores de sentiment pour chaque type en se basant sur le score de base"""
        # Variation aléatoire pour différencier les types (-10 à +10)
        scores = {
            'popularity': min(100, max(0, base_score + random.uniform(-10, 10))),
            'utility': min(100, max(0, base_score + random.uniform(-10, 10))),
            'investment': min(100, max(0, base_score + random.uniform(-10, 10))),
            'stability': min(100, max(0, base_score + random.uniform(-10, 10))),
            'innovation': min(100, max(0, base_score + random.uniform(-10, 10)))
        }
        return scores

    def handle(self, *args, **options):
        self.stdout.write('Starting cryptocurrency sentiment scraping...')
        
        # Initialiser le scraper et l'analyseur de sentiment
        scraper = SocialMediaScraper()
        sentiment_analyzer = SentimentAnalyzer()
        
        # Exécuter le scraping
        scraper.run_scraping()
        
        # Mettre à jour les analyses de sentiment
        cryptocurrencies = Cryptocurrency.objects.all()
        for crypto in cryptocurrencies:
            # Récupérer les posts récents
            recent_posts = SocialMediaPost.objects.filter(
                cryptocurrency=crypto,
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            # Pour chaque post, créer ou mettre à jour les analyses de sentiment
            for post in recent_posts:
                # Calculer le score de sentiment de base
                base_score = sentiment_analyzer.analyze_text(post.content)
                
                # Calculer les scores pour chaque type de sentiment
                sentiment_scores = self.calculate_sentiment_scores(post.content, base_score)
                
                # Créer ou mettre à jour les analyses de sentiment
                for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
                    SentimentAnalysis.objects.update_or_create(
                        post=post,
                        sentiment_type=sentiment_type,
                        defaults={
                            'score': round(sentiment_scores[sentiment_type], 1),
                            'created_at': timezone.now()
                        }
                    )
            
            self.stdout.write(f'Updated sentiment analysis for {crypto.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully completed cryptocurrency sentiment scraping')) 