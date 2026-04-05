FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app

EXPOSE 8501
USER appuser
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
