
FROM python:3.11-slim


WORKDIR /app


RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    postgresql-client \
    wget \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*


RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc \
    && chmod +x mc \
    && mv mc /usr/local/bin/


COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/0
ENV DJANGO_SETTINGS_MODULE=root.settings


ENTRYPOINT ["/entrypoint.sh"]


EXPOSE 8001  # Django/Daphne (HTTP + WebSocket)
