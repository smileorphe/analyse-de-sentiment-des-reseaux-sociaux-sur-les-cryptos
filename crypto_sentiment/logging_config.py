import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configuration du logger principal
    logger = logging.getLogger('crypto_sentiment')
    logger.setLevel(logging.INFO)

    # Handler pour le fichier
    file_handler = RotatingFileHandler(
        'logs/scraping.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format des messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Ajouter les handlers au logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 