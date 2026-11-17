FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
# команда задається в docker-compose.yml (web, sync-worker, data-loader, app-init)
CMD ["python", "-m", "src.entrypoints.web"]
