from django.core.management.base import BaseCommand
from crypto_sentiment.models import SocialMediaPost

class Command(BaseCommand):
    help = 'Nettoie les posts de test de la base de données'

    def handle(self, *args, **kwargs):
        # Supprimer tous les posts qui commencent par "Post de test"
        count = SocialMediaPost.objects.filter(content__startswith='Post de test').delete()[0]
        self.stdout.write(f'Suppression de {count} posts de test effectuée avec succès.')
