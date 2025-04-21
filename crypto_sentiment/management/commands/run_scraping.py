from django.core.management.base import BaseCommand
from crypto_sentiment.scrapers import SocialMediaScraper
from crypto_sentiment.tasks import analyze_sentiments
from crypto_sentiment.logging_config import setup_logging

class Command(BaseCommand):
    help = 'Exécute le scraping des réseaux sociaux et analyse les sentiments'

    def handle(self, *args, **options):
        # Configurer le logging
        logger = setup_logging()
        
        logger.info('Démarrage du scraping des réseaux sociaux...')
        
        # Exécuter le scraping
        try:
            scraper = SocialMediaScraper()
            scraper.run_scraping()
            logger.info('Scraping terminé avec succès')
        except Exception as e:
            logger.error(f'Erreur lors du scraping: {str(e)}')
        
        # Analyser les sentiments
        logger.info('Démarrage de l\'analyse des sentiments...')
        try:
            analyze_sentiments()
            logger.info('Analyse des sentiments terminée')
        except Exception as e:
            logger.error(f'Erreur lors de l\'analyse des sentiments: {str(e)}') 