#!/bin/bash

# Vérifier si les variables d'environnement sont définies
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "Erreur: FLASK_SECRET_KEY n'est pas définie"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Erreur: GOOGLE_API_KEY n'est pas définie"
    exit 1
fi

# Définir l'environnement de production
export FLASK_ENV=production
export FLASK_APP=app.py

# Démarrer Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 120 --access-logfile access.log --error-logfile error.log wsgi:app 