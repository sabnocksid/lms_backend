FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy requirements.txt from lms_project folder
COPY /requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire lms_project folder into /app
COPY lms_project/ ./lms_project/

# Copy wait-for-it.sh if you have it in root folder (next to Dockerfile)
COPY wait-for-it.sh .

RUN chmod +x wait-for-it.sh



