#!/usr/bin/env bash
# StandardBridge — production ishga tushirish skripti (Railway).
# Procfile va Railway Custom Start Command shuni chaqiradi.
set -e  # biror buyruq xato bersa to'xtaydi

echo "==> Migratsiyalar..."
python manage.py migrate --noinput

echo "==> Statik fayllar..."
python manage.py collectstatic --noinput

echo "==> Boshlang'ich ma'lumotlar (idempotent)..."
python manage.py seed_data
python manage.py seed_questions
python manage.py load_checklist
python manage.py load_expert_templates
python manage.py seed_experts
python manage.py create_admin

echo "==> Gunicorn ishga tushmoqda..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 300
