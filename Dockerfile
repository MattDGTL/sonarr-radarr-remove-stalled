FROM python:3.9-slim-buster

ENV SONARR_URL='http://192.168.0.45:8989'
ENV SONARR_API_KEY=e17da5ef3e5a433c8644deb986e99089
ENV RADARR_URL='http://192.168.0.45:7878'
ENV RADARR_API_KEY=d4e7c8f44daa4da083b8be00da697651
ENV TIMEOUT=600

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "cleaner.py"]
