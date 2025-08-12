#!/bin/sh

set -e

echo "🚀 Waiting for PostgreSQL..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done
echo "✅ PostgreSQL is ready."

echo "📦 Creating database if it does not exist..."
python create_db.py

echo "📦 Making migrations (checking for errors)..."
if ! python manage.py makemigrations --noinput; then
  echo "❌ makemigrations failed. You might have added a non-nullable field without a default."
  echo "👉 Fix your model by either:"
  echo "   - adding null=True,"
  echo "   - or setting a default=...,"
  echo "   - or manually running makemigrations without --noinput to provide one-off defaults."
  exit 1
fi

echo "📦 Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn server..."
exec gunicorn root.wsgi:application --bind 0.0.0.0:8001
