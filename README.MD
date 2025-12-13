# Lumo LMS

A modern, dockerized Learning Management System (LMS) built with Django, Celery, Redis, PostgreSQL, and MinIO. Supports user management, courses, assignments, asynchronous task processing, and media storage.

![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Setup & Configuration](#setup--configuration)
5. [Environment Variables](#environment-variables)
6. [Docker Compose Configuration](#docker-compose-configuration)
7. [Running the Application](#running-the-application)
8. [Accessing Services](#accessing-services)
9. [Common Commands](#common-commands)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

---

## 🎓 Introduction

Lumo LMS provides a modular, scalable platform for online education. Built with modern technologies and containerized for easy deployment, it offers a complete solution for managing online courses, students, and educational content.

---

## ✨ Features

- 🎯 **User Management**: Role-based authentication (students, instructors, admins)
- 📚 **Course Management**: Create, organize, and manage courses
- 📝 **Assignments & Assessments**: Automated grading and feedback
- ⚡ **Asynchronous Task Processing**: Background jobs via Celery & Redis
- 💾 **PostgreSQL Database**: Robust and scalable data storage
- 🗄️ **MinIO Storage**: S3-compatible media and file management
- 📊 **Admin Dashboard**: pgAdmin for database management
- ⏰ **Task Scheduling**: Celery Beat for periodic tasks
- 🐳 **Fully Dockerized**: Easy deployment and scaling

---

## 📦 Prerequisites

Before setting up Lumo LMS, ensure you have:

- **Docker** ≥ 20.x ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** ≥ 2.x ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git** ([Install Git](https://git-scm.com/downloads))
- At least **4GB RAM** for smooth operation

---

## 🚀 Setup & Configuration

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lumo-lms.git
cd lumo-lms
```

### 2. Create Environment File

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Then edit `.env` with your configurations (see [Environment Variables](#environment-variables) section).

### 3. Build and Start Services

```bash
docker-compose up --build
```

### 4. Apply Database Migrations

```bash
docker exec -it lms_app python manage.py migrate
```

### 5. Create Django Superuser

```bash
docker exec -it lms_app python manage.py createsuperuser
```

### 6. Create MinIO Bucket (Optional)

Access MinIO console at `http://localhost:9001` and create a bucket named `lms-media`, or run:

```bash
docker exec -it minio mc alias set myminio http://localhost:9000 minioadmin minio123
docker exec -it minio mc mb myminio/lms-media
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# PostgreSQL Configuration
POSTGRES_DB=lms_db
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=strongpassword123

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio123
MINIO_BUCKET=lms-media

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin123

# Django Configuration
DJANGO_SECRET_KEY=your-django-secret-key-here-generate-a-strong-one
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

> ⚠️ **Security Note**: Never commit `.env` file to version control. Add it to `.gitignore`.

---

## 🐳 Docker Compose Configuration

The `docker-compose.yml` file defines the following services:

### Services Overview

| Service | Container Name | Port(s) | Description |
|---------|---------------|---------|-------------|
| **web** | lms_app | 8001 | Django application (Daphne ASGI server) |
| **lms_celery** | lms_celery | - | Celery worker for async tasks |
| **lms_celery_beat** | lms_celery_beat | - | Celery Beat scheduler |
| **redis** | redis | 6379 | Message broker for Celery |
| **db** | lms_db | 5432 | PostgreSQL database |
| **minio** | minio | 9000, 9001 | S3-compatible object storage |
| **pgadmin** | pgadmin | 8080 | PostgreSQL admin interface |

### Complete Docker Compose Configuration

```yaml
version: '3.9'

services:
  web:
    build: .
    container_name: lms_app
    command: daphne -b 0.0.0.0 -p 8001 root.asgi:application
    ports:
      - "8001:8001"
    env_file:
      - .env
    depends_on:
      - db
      - minio
      - redis
    volumes:
      - .:/app
    entrypoint: ["/entrypoint.sh"]

  lms_celery:
    build: .
    container_name: lms_celery
    command: celery -A root worker -l info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    entrypoint: ["/entrypoint.sh"]

  lms_celery_beat:
    build: .
    container_name: lms_celery_beat
    command: celery -A root beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    entrypoint: ["/entrypoint.sh"]

  # Redis
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"

  # PostgreSQL
  db:
    image: postgres:15
    container_name: lms_db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  # MinIO
  minio:
    image: minio/minio
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

  # pgAdmin
  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD}
    ports:
      - "8080:80"
    depends_on:
      - db

volumes:
  pgdata:
  minio_data:
```

---

## 🎮 Running the Application

### Start All Services

```bash
docker-compose up
```

Or run in detached mode:

```bash
docker-compose up -d
```

### Build and Start (First Time or After Changes)

```bash
docker-compose up --build
```

### Stop Services

```bash
docker-compose down
```

### Stop Services and Remove Volumes (⚠️ Deletes Data)

```bash
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f lms_celery
```

---

## 🌐 Accessing Services

Once running, access the following services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django App** | http://localhost:8001 | Use created superuser |
| **Django Admin** | http://localhost:8001/admin | Use created superuser |
| **MinIO Console** | http://localhost:9001 | minioadmin / minio123 |
| **MinIO API** | http://localhost:9000 | - |
| **pgAdmin** | http://localhost:8080 | admin@example.com / admin123 |
| **Redis** | localhost:6379 | - |
| **PostgreSQL** | localhost:5432 | lms_user / strongpassword123 |

---

## 🛠️ Common Commands

### Django Commands

```bash
# Run migrations
docker exec -it lms_app python manage.py migrate

# Create superuser
docker exec -it lms_app python manage.py createsuperuser

# Collect static files
docker exec -it lms_app python manage.py collectstatic --noinput

# Run Django shell
docker exec -it lms_app python manage.py shell

# Create new app
docker exec -it lms_app python manage.py startapp appname
```

### Database Commands

```bash
# Database backup
docker exec lms_db pg_dump -U lms_user lms_db > backup.sql

# Database restore
cat backup.sql | docker exec -i lms_db psql -U lms_user -d lms_db
```

### Celery Commands

```bash
# View Celery worker status
docker exec -it lms_celery celery -A root inspect active

# Purge all tasks
docker exec -it lms_celery celery -A root purge
```

### Docker Commands

```bash
# Rebuild specific service
docker-compose up --build web

# Restart specific service
docker-compose restart web

# View running containers
docker-compose ps

# Access container shell
docker exec -it lms_app bash

# Remove all stopped containers
docker-compose rm
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8001
# or
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>
```

### Database Connection Error

1. Ensure PostgreSQL container is running:
   ```bash
   docker-compose ps db
   ```

2. Check database logs:
   ```bash
   docker-compose logs db
   ```

3. Reset database (⚠️ deletes data):
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

### MinIO Bucket Not Found

```bash
# Access MinIO console at http://localhost:9001
# Login with MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
# Create bucket named 'lms-media'
```

### Celery Not Processing Tasks

1. Check Celery worker logs:
   ```bash
   docker-compose logs lms_celery
   ```

2. Ensure Redis is running:
   ```bash
   docker-compose ps redis
   ```

3. Restart Celery:
   ```bash
   docker-compose restart lms_celery lms_celery_beat
   ```

### Permission Denied Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/lumo-lms/issues)
- **Email**: support@lumo-lms.com
- **Documentation**: [Wiki](https://github.com/yourusername/lumo-lms/wiki)

---

## 🙏 Acknowledgments

- Django Framework
- Docker & Docker Compose
- PostgreSQL
- Redis
- MinIO
- Celery

---

Made  by Siddhartha Paudel