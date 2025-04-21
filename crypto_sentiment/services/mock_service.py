import random
from datetime import datetime, timedelta
from ..models import Cryptocurrency, SocialMediaPost

class MockService:
    """
    Service factice pour générer des données de test
    """
    
    def __init__(self):
        self.sentences = [
            "Bitcoin va monter en flèche cette année!",
            "Je suis très optimiste sur l'avenir de l'Ethereum.",
            "Les cryptomonnaies sont une bulle qui va éclater.",
            "J'ai investi tout mon argent dans le Bitcoin, j'espère que ça va marcher.",
            "L'Ethereum est la meilleure cryptomonnaie après le Bitcoin.",
            "Je ne comprends pas pourquoi les gens investissent dans les cryptos.",
            "Le Bitcoin va révolutionner le système financier mondial.",
            "Les cryptomonnaies sont l'avenir de la finance.",
            "Je viens d'acheter du Bitcoin, je suis très content!",
            "L'Ethereum a un grand potentiel pour les applications décentralisées.",
            "Le Bitcoin est trop volatil pour être utilisé comme monnaie.",
            "Les cryptomonnaies sont une arnaque.",
            "J'ai perdu beaucoup d'argent en investissant dans les cryptos.",
            "Le Bitcoin est une réserve de valeur comme l'or.",
            "L'Ethereum va dépasser le Bitcoin dans les prochaines années."
        ]
        
        self.platforms = ['TWITTER', 'REDDIT']
    
    def analyze_sentiment(self, text):
        """
        Analyse de sentiment simplifiée basée sur des mots-clés
        """
        positive_words = ['monter', 'optimiste', 'meilleur', 'avenir', 'content', 'potentiel', 'révolutionner']
        negative_words = ['bulle', 'éclater', 'perdu', 'arnaque', 'volatil', 'ne comprends pas']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return random.uniform(60, 100)
        elif negative_count > positive_count:
            return random.uniform(0, 40)
        else:
            return random.uniform(40, 60)
    
    def generate_mock_posts(self, cryptocurrency, count=20):
        """
        Génère des posts factices pour une cryptomonnaie
        """
        now = datetime.now()
        
        for i in range(count):
            # Générer une date aléatoire dans les 7 derniers jours
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 24)
            minutes_ago = random.randint(0, 60)
            
            created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Sélectionner une phrase aléatoire
            content = random.choice(self.sentences)
            
            # Remplacer Bitcoin/Ethereum par la cryptomonnaie actuelle
            content = content.replace('Bitcoin', cryptocurrency.name)
            content = content.replace('Ethereum', cryptocurrency.name)
            
            # Analyser le sentiment
            sentiment_score = self.analyze_sentiment(content)
            
            # Créer le post
            SocialMediaPost.objects.create(
                cryptocurrency=cryptocurrency,
                platform=random.choice(self.platforms),
                post_id=f"mock_{cryptocurrency.symbol}_{i}",
                content=content,
                sentiment_score=sentiment_score,
                created_at=created_at
            )
    
    def update_all_cryptocurrencies(self):
        """
        Met à jour les données pour toutes les cryptomonnaies
        """
        cryptocurrencies = Cryptocurrency.objects.all()
        
        for crypto in cryptocurrencies:
            try:
                # Supprimer les anciens posts factices
                SocialMediaPost.objects.filter(
                    cryptocurrency=crypto,
                    post_id__startswith="mock_"
                ).delete()
                
                # Générer de nouveaux posts factices
                self.generate_mock_posts(crypto)
                print(f"Données factices générées pour {crypto.symbol}")
            except Exception as e:
                print(f"Erreur lors de la génération des données factices pour {crypto.symbol}: {str(e)}") 