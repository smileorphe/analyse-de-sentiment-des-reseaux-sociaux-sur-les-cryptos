from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sentiment.settings')

app = Celery('Sentiment')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'scrape-social-media': {
        'task': 'crypto_sentiment.tasks.run_social_media_scraping',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    'analyze-sentiments': {
        'task': 'crypto_sentiment.tasks.analyze_sentiments',
        'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
    },
} 