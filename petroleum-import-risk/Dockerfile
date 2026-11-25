# Fuel Import Risk Monitor: API and dashboard share one image.
# Model outputs are not baked in: data/ and reports/ are mounted read-only (see docker-compose.yml).
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-monitor.txt .
RUN pip install --no-cache-dir -r requirements-monitor.txt
COPY config/ config/
COPY src/ src/
RUN useradd --create-home monitor
USER monitor
EXPOSE 8000 8501
