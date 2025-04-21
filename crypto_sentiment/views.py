from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SocialMediaPost, SentimentAnalysis
from django.db.models import Avg, Count
import json
from django.contrib import messages
from django.urls import reverse

def get_sentiment_class(score):
    if score is None:
        return 'secondary'
    if score >= 60:
        return 'success'
    if score <= 40:
        return 'danger'
    return 'warning'

def dashboard(request):
    # Récupérer les cryptomonnaies principales
    cryptocurrencies = Cryptocurrency.objects.all()
    
    # Calculer les statistiques globales
    total_posts = SocialMediaPost.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Calculer les statistiques de sentiment
    sentiment_analyses = SentimentAnalysis.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    # Calculer les pourcentages de sentiment
    positive_posts = sentiment_analyses.filter(score__gte=60).count()
    neutral_posts = sentiment_analyses.filter(score__gte=40, score__lt=60).count()
    negative_posts = sentiment_analyses.filter(score__lt=40).count()
    
    # Calculer les pourcentages
    total_sentiments = positive_posts + neutral_posts + negative_posts
    positive_percentage = round((positive_posts / total_sentiments * 100) if total_sentiments > 0 else 0, 1)
    neutral_percentage = round((neutral_posts / total_sentiments * 100) if total_sentiments > 0 else 0, 1)
    negative_percentage = round((negative_posts / total_sentiments * 100) if total_sentiments > 0 else 0, 1)
    
    # Préparer les données pour le graphique d'évolution
    dates = []
    btc_data = []
    eth_data = []
    
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        dates.insert(0, date.strftime('%d/%m'))
        
        # Calculer la moyenne des sentiments pour BTC
        btc_avg = SentimentAnalysis.objects.filter(
            post__cryptocurrency__symbol='BTC',
            created_at__date=date.date()
        ).aggregate(Avg('score'))['score__avg'] or 50
        btc_data.insert(0, btc_avg)
        
        # Calculer la moyenne des sentiments pour ETH
        eth_avg = SentimentAnalysis.objects.filter(
            post__cryptocurrency__symbol='ETH',
            created_at__date=date.date()
        ).aggregate(Avg('score'))['score__avg'] or 50
        eth_data.insert(0, eth_avg)
    
    # Préparer les données pour les graphiques détaillés
    sentiment_type_data = {}
    sentiment_type_colors = {
        'popularity': '28a745',  # Vert
        'utility': '17a2b8',     # Bleu
        'investment': 'ffc107',  # Jaune
        'stability': 'dc3545',   # Rouge
        'innovation': '6c757d'   # Gris
    }
    
    for sentiment_type, label in SentimentAnalysis.SENTIMENT_TYPES:
        sentiment_type_data[sentiment_type] = []
        for crypto in cryptocurrencies:
            avg_score = SentimentAnalysis.objects.filter(
                post__cryptocurrency=crypto,
                sentiment_type=sentiment_type,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).aggregate(Avg('score'))['score__avg'] or 0
            sentiment_type_data[sentiment_type].append(round(avg_score, 1))
    
    # Ajouter les données de sentiment à chaque cryptomonnaie
    for crypto in cryptocurrencies:
        crypto.sentiments = {}
        crypto.post_count = SocialMediaPost.objects.filter(
            cryptocurrency=crypto,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
            avg_score = SentimentAnalysis.objects.filter(
                post__cryptocurrency=crypto,
                sentiment_type=sentiment_type,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).aggregate(Avg('score'))['score__avg']
            
            if avg_score is not None:
                crypto.sentiments[sentiment_type] = {
                    'score': round(avg_score, 1),
                    'class': get_sentiment_class(avg_score)
                }
            else:
                crypto.sentiments[sentiment_type] = {
                    'score': None,
                    'class': 'secondary'
                }
    
    context = {
        'total_posts': total_posts,
        'positive_posts': positive_posts,
        'neutral_posts': neutral_posts,
        'negative_posts': negative_posts,
        'positive_percentage': positive_percentage,
        'neutral_percentage': neutral_percentage,
        'negative_percentage': negative_percentage,
        'dates': json.dumps(dates),
        'btc_data': json.dumps(btc_data),
        'eth_data': json.dumps(eth_data),
        'sentiment_type_labels': SentimentAnalysis.SENTIMENT_TYPES,
        'sentiment_type_data': json.dumps(sentiment_type_data),
        'sentiment_type_colors': json.dumps(sentiment_type_colors),
        'crypto_symbols': json.dumps([crypto.symbol for crypto in cryptocurrencies]),
        'cryptocurrencies': cryptocurrencies,
        'sentiment_types': [t[0] for t in SentimentAnalysis.SENTIMENT_TYPES],
    }
    
    return render(request, 'crypto_sentiment/dashboard.html', context)

def analysis(request):
    # Récupérer toutes les cryptomonnaies
    cryptocurrencies = Cryptocurrency.objects.all()
    
    # Calculer les statistiques globales
    total_posts = SocialMediaPost.objects.count()
    
    # Calculer les moyennes pour chaque type de sentiment
    sentiment_stats = {}
    for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
        avg_score = SentimentAnalysis.objects.filter(
            sentiment_type=sentiment_type
        ).aggregate(Avg('score'))['score__avg'] or 50
        sentiment_stats[sentiment_type] = round(avg_score, 1)
    
    # Ajouter les données de sentiment à chaque cryptomonnaie
    for crypto in cryptocurrencies:
        crypto.sentiments = {}
        for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
            avg_score = SentimentAnalysis.objects.filter(
                post__cryptocurrency=crypto,
                sentiment_type=sentiment_type
            ).aggregate(Avg('score'))['score__avg']
            
            if avg_score is not None:
                crypto.sentiments[sentiment_type] = {
                    'score': round(avg_score, 1),
                    'class': get_sentiment_class(avg_score)
                }
            else:
                crypto.sentiments[sentiment_type] = {
                    'score': None,
                    'class': 'secondary'
                }
    
    context = {
        'cryptocurrencies': cryptocurrencies,
        'total_posts': total_posts,
        'sentiment_stats': sentiment_stats,
        'sentiment_types': SentimentAnalysis.SENTIMENT_TYPES,
    }
    
    return render(request, 'crypto_sentiment/analysis.html', context)

def crypto_detail(request, crypto_id):
    # Obtenir la cryptomonnaie
    cryptocurrency = get_object_or_404(Cryptocurrency, id=crypto_id)
    
    # Calculer le sentiment actuel
    current_sentiment = SocialMediaPost.objects.filter(
        cryptocurrency=cryptocurrency,
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 50
    
    # Obtenir les posts récents
    recent_posts = SocialMediaPost.objects.filter(
        cryptocurrency=cryptocurrency
    ).order_by('-created_at')[:20]
    
    # Préparer les données pour le graphique
    dates = []
    sentiment_data = []
    
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        dates.insert(0, date.strftime('%d/%m'))
        
        avg = SocialMediaPost.objects.filter(
            cryptocurrency=cryptocurrency,
            created_at__date=date.date()
        ).aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 50
        sentiment_data.insert(0, avg)
    
    context = {
        'cryptocurrency': cryptocurrency,
        'current_sentiment': round(current_sentiment, 1),
        'sentiment_class': get_sentiment_class(current_sentiment),
        'recent_posts': recent_posts,
        'dates': json.dumps(dates),
        'sentiment_data': json.dumps(sentiment_data),
    }
    
    return render(request, 'crypto_sentiment/crypto_detail.html', context)

def posts_list(request):
    posts = SocialMediaPost.objects.select_related('cryptocurrency').order_by('-created_at')
    
    # Filtrer par cryptomonnaie si spécifié
    crypto_symbol = request.GET.get('crypto')
    if crypto_symbol:
        posts = posts.filter(cryptocurrency__symbol=crypto_symbol)
    
    # Filtrer par plateforme si spécifié
    platform = request.GET.get('platform')
    if platform:
        posts = posts.filter(platform=platform)
    
    # Récupérer les cryptomonnaies pour le filtre
    cryptocurrencies = Cryptocurrency.objects.all()
    
    context = {
        'posts': posts,
        'cryptocurrencies': cryptocurrencies,
        'selected_crypto': crypto_symbol,
        'selected_platform': platform,
    }
    
    return render(request, 'crypto_sentiment/posts_list.html', context)

def trigger_scraping(request):
    if request.method == 'POST':
        try:
            from .management.commands.scrape_crypto import Command
            command = Command()
            command.handle()
            messages.success(request, 'Les données ont été mises à jour avec succès!')
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour des données: {str(e)}')
        
        return redirect('crypto_sentiment:analysis')
    return redirect('crypto_sentiment:analysis')
