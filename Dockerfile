FROM python:3.9-slim-buster

ENV SONARR_URL='http://sonarr:9696'
ENV SONARR_API_KEY=123
ENV RADARR_URL='http://radarr:7878'
ENV RADARR_API_KEY=d4e7c8f44daa4da083b8be00da697651
ENV TIMEOUT=600

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "cleaner.py"]
