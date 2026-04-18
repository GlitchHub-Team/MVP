# Avvio sistema

Per avviare il sistema, eseguire il comando:
```bash
docker compose --env-file Infrastructure/.env  --env-file .env up -d
```

# Esecuzione test di sistema
```bash
docker compose --env-file Infrastructure/.env  --env-file .env -f docker-compose.yml exec -T -e APP_URL=http://frontend -e PYTHONDONTWRITEBYTECODE=1 e2e-tests python -B -m pytest -q tests
```