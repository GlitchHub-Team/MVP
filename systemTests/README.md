# Comando esecuzione tests
```bash
docker compose --env-file Infrastructure/.env  --env-file .env -f docker-compose.yml exec -T -e APP_URL=http://frontend -e PYTHONDONTWRITEBYTECODE=1 e2e-tests python -B -m pytest -q tests
```