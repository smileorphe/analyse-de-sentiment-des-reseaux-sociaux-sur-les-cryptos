from celery import shared_task
from .scrapers import SocialMediaScraper
from .models import SocialMediaPost
from textblob import TextBlob
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_social_media_scraping():
    """Tâche périodique pour exécuter le scraping des réseaux sociaux"""
    try:
        scraper = SocialMediaScraper()
        scraper.run_scraping()
        logger.info("Scraping des réseaux sociaux terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du scraping des réseaux sociaux: {str(e)}")

@shared_task
def analyze_sentiments():
    """Tâche périodique pour analyser les sentiments des posts non analysés"""
    try:
        # Récupérer les posts qui n'ont pas encore été analysés
        unanalyzed_posts = SocialMediaPost.objects.filter(sentiment_score__isnull=True)
        
        for post in unanalyzed_posts:
            # Combiner le titre et le contenu pour l'analyse
            text = f"{post.title} {post.content}"
            
            # Analyser le sentiment avec TextBlob
            analysis = TextBlob(text)
            
            # Convertir le sentiment (-1 à 1) en pourcentage (0 à 100)
            sentiment_score = (analysis.sentiment.polarity + 1) * 50
            
            # Mettre à jour le post avec le score de sentiment
            post.sentiment_score = sentiment_score
            post.save()
            
        logger.info(f"Analyse des sentiments terminée pour {unanalyzed_posts.count()} posts")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des sentiments: {str(e)}") 