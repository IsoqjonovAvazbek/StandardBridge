#!/usr/bin/env bash
# StandardBridge — production ishga tushirish skripti (Railway).
# Procfile va Railway Custom Start Command shuni chaqiradi.
set -e  # biror buyruq xato bersa to'xtaydi

echo "==> Migratsiyalar..."
python manage.py migrate --noinput

echo "==> Statik fayllar..."
python manage.py collectstatic --noinput

echo "==> Boshlang'ich ma'lumotlar (idempotent)..."
python manage.py seed_data || echo "seed_data xato (o'tkazib yuborildi)"
python manage.py seed_standards || echo "seed_standards xato (o'tkazib yuborildi)"
python manage.py seed_questions || echo "seed_questions xato (o'tkazib yuborildi)"
python manage.py load_checklist || echo "load_checklist xato (o'tkazib yuborildi)"
python manage.py load_expert_templates || echo "load_expert_templates xato (o'tkazib yuborildi)"
python manage.py seed_experts || echo "seed_experts xato (o'tkazib yuborildi)"
python manage.py seed_roadmap_steps || echo "seed_roadmap_steps xato (o'tkazib yuborildi)"
python manage.py seed_blog_posts || echo "seed_blog_posts xato (o'tkazib yuborildi)"
python manage.py create_admin || echo "create_admin xato (o'tkazib yuborildi)"
python manage.py setup_telegram_webhook || echo "setup_telegram_webhook xato (o'tkazib yuborildi)"

echo "==> Gunicorn ishga tushmoqda..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 300
