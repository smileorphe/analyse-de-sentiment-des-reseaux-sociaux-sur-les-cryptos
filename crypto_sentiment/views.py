from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from .models import Cryptocurrency, SocialMediaPost, SentimentAnalysis
from django.db.models import Avg, Count
import json
from django.contrib import messages
from django.urls import reverse
import itertools
import numpy
from collections import Counter
import re
from nltk.corpus import stopwords
import nltk

def get_sentiment_class(score):
    if score is None:
        return 'secondary'
    if score >= 60:
        return 'success'
    if score <= 40:
        return 'danger'
    return 'warning'

def calculate_correlations(sentiment_data):
    """
    Calcule la matrice de corrélation entre les cryptos basée sur leurs sentiments
    """
    correlations = {}
    crypto_pairs = list(itertools.combinations(sentiment_data.keys(), 2))
    
    for crypto1, crypto2 in crypto_pairs:
        # Calculer la corrélation seulement si les deux séries ont des données
        if sentiment_data[crypto1] and sentiment_data[crypto2]:
            correlation = round(
                numpy.corrcoef(sentiment_data[crypto1], sentiment_data[crypto2])[0, 1],
                2
            )
        else:
            correlation = 0
            
        if crypto1 not in correlations:
            correlations[crypto1] = {}
        if crypto2 not in correlations:
            correlations[crypto2] = {}
            
        correlations[crypto1][crypto2] = correlation
        correlations[crypto2][crypto1] = correlation
        
    # Ajouter l'auto-corrélation (1.0) pour chaque crypto
    for crypto in sentiment_data.keys():
        if crypto not in correlations:
            correlations[crypto] = {}
        correlations[crypto][crypto] = 1.0
        
    return correlations

def extract_keywords(text):
    """Extrait les mots-clés d'un texte en ignorant les mots courants"""
    # Télécharger les stopwords si nécessaire
    try:
        stop_words = set(stopwords.words('english'))
    except LookupError:
        nltk.download('stopwords')
        stop_words = set(stopwords.words('english'))
    
    # Ajouter des stopwords spécifiques aux cryptos
    crypto_stop_words = {'crypto', 'cryptocurrency', 'coin', 'token', 'price', 'buy', 'sell'}
    stop_words.update(crypto_stop_words)
    
    # Nettoyer et tokenizer le texte
    text = text.lower()
    words = re.findall(r'\b[a-z]+\b', text)
    
    # Filtrer les stopwords et les mots courts
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords

def calculate_word_sentiments(posts_with_sentiment):
    """Calcule le sentiment moyen pour chaque mot"""
    word_sentiments = {}
    word_counts = Counter()
    
    for post, score in posts_with_sentiment:
        keywords = extract_keywords(post.content)
        for word in keywords:
            if word not in word_sentiments:
                word_sentiments[word] = []
            word_sentiments[word].append(score)
            word_counts[word] += 1
    
    # Calculer le sentiment moyen et préparer les données
    word_data = []
    for word, count in word_counts.most_common(100):  # Limiter aux 100 mots les plus fréquents
        if count >= 2:  # Ignorer les mots qui n'apparaissent qu'une fois
            avg_sentiment = sum(word_sentiments[word]) / len(word_sentiments[word])
            word_data.append({
                'text': word,
                'size': count,
                'sentiment': avg_sentiment,
                'color': get_sentiment_color(avg_sentiment)
            })
    
    return word_data

def get_sentiment_color(score):
    """Retourne une couleur RGB basée sur le score de sentiment"""
    if score >= 60:
        # Vert pour positif
        intensity = min((score - 60) / 40, 1)
        return f'rgb(0, {int(200 * intensity)}, 0)'
    elif score <= 40:
        # Rouge pour négatif
        intensity = min((40 - score) / 40, 1)
        return f'rgb({int(200 * intensity)}, 0, 0)'
    else:
        # Gris pour neutre
        return 'rgb(128, 128, 128)'

def dashboard(request):
    # Récupérer les paramètres de filtre
    period = request.GET.get('period', '7d')  # Par défaut 7 jours
    source = request.GET.get('source', 'all')  # Par défaut toutes les sources
    
    # Déterminer la période de filtrage
    now = timezone.now()
    if period == '24h':
        start_date = now - timedelta(hours=24)
    elif period == '7d':
        start_date = now - timedelta(days=7)
    elif period == '30d':
        start_date = now - timedelta(days=30)
    elif period == '90d':
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=7)  # Par défaut 7 jours
    
    # Récupérer les cryptomonnaies principales
    cryptocurrencies = Cryptocurrency.objects.all()
    
    # Préparer la requête de base pour les posts
    posts_query = SocialMediaPost.objects.filter(created_at__gte=start_date)
    
    # Filtrer par source si nécessaire
    if source != 'all':
        posts_query = posts_query.filter(platform__iexact=source)
    
    # Calculer les statistiques globales
    total_posts = posts_query.count()
    
    # Calculer les statistiques de sentiment
    sentiment_analyses = SentimentAnalysis.objects.filter(
        post__in=posts_query
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
    crypto_data = {}
    crypto_colors = {
        'BTC': '#f7931a',  # Orange Bitcoin
        'ETH': '#627eea',  # Bleu Ethereum
        'XRP': '#00aae4',  # Bleu Ripple
        'ADA': '#0033ad',  # Bleu Cardano
        'SOL': '#00ffa3',  # Vert Solana
        'DOT': '#e6007a',  # Rose Polkadot
        'DOGE': '#ba9f33', # Or Dogecoin
        'AVAX': '#e84142', # Rouge Avalanche
        'LINK': '#2a5ada', # Bleu Chainlink
        'MATIC': '#8247e5', # Violet Polygon
    }
    
    # Initialiser les données pour chaque crypto
    for crypto in cryptocurrencies:
        crypto_data[crypto.symbol] = []
    
    # Déterminer l'intervalle des points de données
    if period == '24h':
        interval = timedelta(hours=1)
        format_string = '%H:%M'
        points = 24
    elif period == '7d':
        interval = timedelta(days=1)
        format_string = '%d/%m'
        points = 7
    elif period == '30d':
        interval = timedelta(days=2)
        format_string = '%d/%m'
        points = 15
    else:  # 90d
        interval = timedelta(days=6)
        format_string = '%d/%m'
        points = 15
    
    # Collecter les données pour toutes les cryptos
    sentiment_data = {crypto.symbol: [] for crypto in cryptocurrencies}
    
    for i in range(points):
        end_date = now - (i * interval)
        start_date_point = end_date - interval
        dates.insert(0, end_date.strftime(format_string))
        
        for crypto in cryptocurrencies:
            # Filtrer les analyses pour cette période et cette crypto
            period_analyses = sentiment_analyses.filter(
                post__cryptocurrency=crypto,
                created_at__gte=start_date_point,
                created_at__lt=end_date
            )
            
            avg_score = period_analyses.aggregate(Avg('score'))['score__avg'] or 50
            score = round(avg_score, 1)
            crypto_data[crypto.symbol].insert(0, score)
            sentiment_data[crypto.symbol].append(score)
    
    # Calculer les corrélations
    correlations = calculate_correlations(sentiment_data)
    
    # Ajouter les données de sentiment à chaque cryptomonnaie
    for crypto in cryptocurrencies:
        crypto.sentiments = {}
        crypto.post_count = posts_query.filter(cryptocurrency=crypto).count()
        
        for sentiment_type, _ in SentimentAnalysis.SENTIMENT_TYPES:
            avg_score = sentiment_analyses.filter(
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
    
    # Récupérer les posts avec leurs scores de sentiment pour le nuage de mots
    posts_with_sentiment = []
    for post in posts_query:
        sentiment = SentimentAnalysis.objects.filter(post=post).aggregate(Avg('score'))['score__avg']
        if sentiment is not None:
            posts_with_sentiment.append((post, sentiment))
    
    # Calculer les données pour le nuage de mots
    word_data = calculate_word_sentiments(posts_with_sentiment)
    
    # Préparer les options de filtre pour le template
    period_options = [
        ('24h', 'Dernières 24 heures'),
        ('7d', '7 derniers jours'),
        ('30d', '30 derniers jours'),
        ('90d', '90 derniers jours'),
    ]
    
    source_options = [
        ('all', 'Toutes les sources'),
        ('reddit', 'Reddit'),
        ('4chan', '4chan'),
    ]
    
    context = {
        'cryptocurrencies': cryptocurrencies,
        'total_posts': total_posts,
        'positive_percentage': positive_percentage,
        'neutral_percentage': neutral_percentage,
        'negative_percentage': negative_percentage,
        'dates': json.dumps(dates),
        'crypto_data': json.dumps(crypto_data),
        'crypto_colors': json.dumps(crypto_colors),
        'sentiment_types': SentimentAnalysis.SENTIMENT_TYPES,
        # Options de filtre
        'period_options': period_options,
        'source_options': source_options,
        'selected_period': period,
        'selected_source': source,
        'correlations': json.dumps(correlations),
        'crypto_symbols': json.dumps([c.symbol for c in cryptocurrencies]),
        'word_data': json.dumps(word_data),
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
        posts = posts.filter(platform__iexact=platform)  # Utiliser iexact pour une comparaison insensible à la casse
    
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

def landing(request):
    """Vue pour la landing page avec animations GSAP"""
    return render(request, 'crypto_sentiment/landing.html')
