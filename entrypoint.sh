#!/bin/sh
set -e

# Wait for Postgres
echo "⏳ Waiting for Postgres..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ Postgres is up"

# Only run migrations & collectstatic if running Django web
if [ "$1" = "runserver" ] || [ "$1" = "gunicorn" ]; then
  echo "📦 Applying Django migrations..."
  python manage.py migrate --noinput

  echo "🗂 Collecting static files..."
  python manage.py collectstatic --noinput

  echo "☁️ Configuring MinIO..."
  mc alias set local $MY_S3_ENDPOINT_URL $MY_ACCESS_KEY_ID $MY_SECRET_KEY
  mc mb --ignore-existing local/$MY_BUCKET_NAME
  mc mb --ignore-existing local/$MY_BUCKET_NAME/lessons/videos
  mc mb --ignore-existing local/$MY_BUCKET_NAME/lessons/materials

  echo "✅ MinIO setup complete"
fi

# Execute the passed command (web server, celery, celery beat)
echo "🚀 Starting: $@"
exec "$@"
