from django.db import models
from django.utils import timezone

# Create your models here.

class Cryptocurrency(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class SocialMediaPost(models.Model):
    PLATFORM_CHOICES = [
        ('reddit', 'Reddit'),
        ('4chan', '4chan'),
    ]

    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    content = models.TextField()
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(default=timezone.now)
    sentiment_score = models.FloatField(null=True, blank=True)
    post_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.cryptocurrency.symbol} - {self.platform} - {self.created_at}"

class SentimentAnalysis(models.Model):
    SENTIMENT_TYPES = [
        ('popularity', 'Popularité'),
        ('utility', 'Utilité'),
        ('investment', 'Potentiel d\'investissement'),
        ('stability', 'Stabilité'),
        ('innovation', 'Innovation'),
    ]

    post = models.ForeignKey(SocialMediaPost, on_delete=models.CASCADE, related_name='sentiment_analyses')
    sentiment_type = models.CharField(max_length=20, choices=SENTIMENT_TYPES)
    score = models.FloatField(default=50.0)  # Score de 0 à 100
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['post', 'sentiment_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.post.cryptocurrency.symbol} - {self.get_sentiment_type_display()} - {self.score}%"
