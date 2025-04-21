from django import template

register = template.Library()

@register.filter
def get_sentiment_class(score):
    if score is None:
        return 'secondary'
    if score >= 60:
        return 'success'
    if score <= 40:
        return 'danger'
    return 'warning'

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) 