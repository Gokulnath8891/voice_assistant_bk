# Docker Deployment Guide

## Prerequisites
- Docker installed and running
- Docker Compose installed

## Quick Start

1. **Setup environment variables:**
   ```bash
   cp .env.docker .env
   # Edit .env with your actual Azure credentials
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build -d
   ```

3. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs voice-api
   ```

4. **Access the API:**
   - Voice API: http://localhost:8000
   - Admin: http://localhost:8000/admin/

## API Endpoints

### Speech Recognition
```bash
curl -X POST http://localhost:8000/api/v1/speech/recognize \
  -F "audio=@your_audio_file.wav"
```

### Semantic Search
```bash
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the airbag work?"}'
```

### Text-to-Speech
```bash
curl -X POST http://localhost:8000/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice_settings": {"voice": "default", "rate": 150, "volume": 0.8}}'
```

## Management Commands

### Stop services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f voice-api
```

### Rebuild after code changes:
```bash
docker-compose up --build -d
```

### Run Django management commands:
```bash
docker-compose exec voice-api python manage.py migrate
docker-compose exec voice-api python manage.py createsuperuser
docker-compose exec voice-api python manage.py collectstatic
```

### Populate vector database:
```bash
docker-compose exec voice-api python pdf_to_vectordb.py pdf_docs/
```

## Production Deployment

For production deployment:

1. **Set proper environment variables in .env:**
   - Set `DEBUG=False`
   - Use a strong `SECRET_KEY`
   - Configure proper `ALLOWED_HOSTS` in settings.py

2. **Use a reverse proxy (nginx):**
   ```yaml
   # Add to docker-compose.yml
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
     depends_on:
       - voice-api
   ```

3. **Add persistent storage:**
   ```yaml
   volumes:
     - ./data:/app/data
     - ./logs:/app/logs
   ```

## Troubleshooting

### Container won't start:
```bash
docker-compose logs voice-api
```

### Audio issues:
- Ensure audio files are in WAV format
- Check Azure Speech Service credentials

### Vector database empty:
```bash
docker-compose exec voice-api python pdf_to_vectordb.py pdf_docs/
```

### Permission issues:
```bash
sudo chown -R $USER:$USER ./my_vector_db
sudo chown -R $USER:$USER ./tesla_db
```