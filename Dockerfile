FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[dev]"
ENTRYPOINT ["samsara-driver-sync"]
