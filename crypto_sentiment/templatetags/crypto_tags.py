from django import template

register = template.Library()

@register.filter
def get_sentiment_class(score):
    if score is None:
        return 'secondary'  # Gris pour les valeurs manquantes
    if score >= 75:
        return 'success'    # Vert pour très positif
    elif score >= 60:
        return 'info'       # Bleu pour positif
    elif score >= 40:
        return 'warning'    # Jaune pour neutre
    else:
        return 'danger'     # Rouge pour négatif 