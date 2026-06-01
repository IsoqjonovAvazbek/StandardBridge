release: python manage.py migrate --noinput
web: python manage.py migrate --noinput && python manage.py seed_questions && python manage.py load_checklist && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
