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
  echo "❌ makemigrations failed."
  exit 1
fi

echo "📦 Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# -----------------------------
# MinIO bucket creation
# -----------------------------
echo "☁️ Creating MinIO bucket if it does not exist..."
# Only install mc if not present (optional if already baked in Dockerfile)
if ! command -v mc >/dev/null 2>&1; then
  echo "📦 Installing MinIO client..."
  curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  chmod +x mc
  mv mc /usr/local/bin/
fi

# wait a few seconds for MinIO to start
sleep 5

# Set alias and create bucket
mc alias set local-minio http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc mb local-minio/$AWS_STORAGE_BUCKET_NAME || true

echo "✅ MinIO bucket ready."

echo "🚀 Starting Gunicorn server..."
exec gunicorn root.wsgi:application --bind 0.0.0.0:8001
