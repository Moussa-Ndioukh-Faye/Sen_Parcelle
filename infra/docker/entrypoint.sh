#!/bin/sh
set -e

echo "→ Initialisation Sen_parcelle (single container)..."

cd /app/backend

echo "→ Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear 2>&1

echo "→ Migration de la base de données..."
python manage.py migrate --noinput 2>&1

echo "→ Création du superadmin si inexistant..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        'admin@sen-parcelle.sn',
        '0000000000',
        'admin123',
        nom='Admin',
        role='admin'
    )
    print('✓ Superadmin créé: admin@sen-parcelle.sn / admin123')
else:
    print('✓ Superadmin déjà existant')
" 2>&1

echo "→ Ajustement des permissions..."
chown -R sen_parcelle:sen_parcelle /data /var/log/supervisor /var/run

echo "→ Démarrage des services (Nginx + Gunicorn)..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/senparcelle.conf
