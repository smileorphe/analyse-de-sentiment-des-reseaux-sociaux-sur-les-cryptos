from django.core.management.base import BaseCommand
from crypto_sentiment.models import Cryptocurrency, SocialMediaPost, SentimentAnalysis
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Ajoute des données initiales pour les tests'

    def handle(self, *args, **kwargs):
        # Supprimer toutes les données existantes
        SentimentAnalysis.objects.all().delete()
        SocialMediaPost.objects.all().delete()
        Cryptocurrency.objects.all().delete()

        # Créer des cryptomonnaies
        cryptocurrencies = [
            ('Bitcoin', 'BTC'),
            ('Ethereum', 'ETH'),
            ('Cardano', 'ADA'),
            ('Solana', 'SOL'),
            ('Polkadot', 'DOT'),
        ]

        for name, symbol in cryptocurrencies:
            crypto = Cryptocurrency.objects.create(
                name=name,
                symbol=symbol
            )
            self.stdout.write(f'Création de {name} ({symbol})')

            # Créer des posts et des analyses pour chaque cryptomonnaie
            for platform in ['reddit', '4chan']:
                for i in range(3):
                    # Créer un score de sentiment aléatoire pour le post
                    sentiment_score = random.uniform(30, 70)
                    
                    post = SocialMediaPost.objects.create(
                        cryptocurrency=crypto,
                        content=f'Post de test {i+1} sur {crypto.name}',
                        platform=platform,
                        post_id=f'{platform}_{crypto.symbol}_{i+1}',
                        sentiment_score=round(sentiment_score, 1)
                    )

                    # Créer des analyses de sentiment pour chaque post
                    for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
                        score = random.uniform(30, 70)  # Score aléatoire entre 30 et 70
                        SentimentAnalysis.objects.create(
                            post=post,
                            sentiment_type=sentiment_type,
                            score=round(score, 1)
                        )

        self.stdout.write(self.style.SUCCESS('Données initiales créées avec succès!')) 