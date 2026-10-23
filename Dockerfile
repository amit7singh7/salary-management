FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 DATABASE=/data/salary.db PORT=8000
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY frontend frontend
RUN mkdir -p /data
WORKDIR /app/backend
EXPOSE 8000
# Seeds 10,000 employees on first boot only, then serves API + UI from one process.
CMD ["sh", "-c", "python seed.py --if-empty && exec gunicorn -w 2 -b 0.0.0.0:${PORT} 'app:create_app()'"]
