from django.core.management.base import BaseCommand
from crypto_sentiment.services.mock_service import MockService

class Command(BaseCommand):
    help = 'Met à jour les données de sentiment des cryptomonnaies'

    def handle(self, *args, **options):
        self.stdout.write('Début de la mise à jour des données de sentiment...')
        
        mock_service = MockService()
        mock_service.update_all_cryptocurrencies()
        
        self.stdout.write(self.style.SUCCESS('Mise à jour terminée avec succès!')) 