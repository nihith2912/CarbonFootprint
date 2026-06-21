# Build python django backend container
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose Django port
EXPOSE 8000

# Run migrations, collect static, and run Gunicorn
CMD ["sh", "-c", "python backend/manage.py makemigrations api && python backend/manage.py migrate && python backend/manage.py seed_data && python backend/manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 --chdir backend ecotrack.wsgi:application"]
