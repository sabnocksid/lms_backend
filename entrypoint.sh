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

echo "☁️  Creating MinIO bucket if it does not exist..."
if ! command -v mc >/dev/null 2>&1; then
  echo "📦 Installing MinIO client..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  mv mc /usr/local/bin/
fi

sleep 5

echo "☁️  Creating MinIO bucket if it does not exist..."
if ! command -v mc >/dev/null 2>&1; then
  echo "📦 Installing MinIO client..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  mv mc /usr/local/bin/
fi

sleep 5

mc alias set local-minio http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

mc mb local-minio/$AWS_STORAGE_BUCKET_NAME || true

echo "✅ MinIO bucket ready."

echo "🚀 Starting Gunicorn server..."
exec gunicorn root.wsgi:application --bind 0.0.0.0:8001
