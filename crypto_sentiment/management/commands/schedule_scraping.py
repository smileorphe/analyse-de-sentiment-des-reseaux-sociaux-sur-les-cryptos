from django.core.management.base import BaseCommand
import subprocess
import time
import logging
import os
import sys

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Planifie l\'exécution régulière du scraping et de l\'analyse des sentiments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalle en minutes entre chaque exécution (défaut: 30)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(self.style.SUCCESS(f'Planification du scraping toutes les {interval} minutes...'))
        
        try:
            while True:
                # Exécuter la commande de scraping
                self.stdout.write(self.style.SUCCESS('Exécution du scraping...'))
                subprocess.run([sys.executable, 'manage.py', 'run_scraping'], check=True)
                
                # Attendre l'intervalle spécifié
                self.stdout.write(self.style.SUCCESS(f'Attente de {interval} minutes avant la prochaine exécution...'))
                time.sleep(interval * 60)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Planification arrêtée par l\'utilisateur'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}')) 