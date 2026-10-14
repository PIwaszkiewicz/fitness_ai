# Obraz serwera API Fitness AI.
# Budowa: docker build -t fitness-ai .   Uruchomienie całości: docker compose up

# Lekka wersja Pythona 3.12 (ta sama wersja co lokalnie i w CI).
FROM python:3.12-slim

# Bez plików .pyc i z natychmiastowym wypisywaniem logów (bez buforowania).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Najpierw same zależności: Docker zapamiętuje tę warstwę i przy zmianie
# samego kodu nie instaluje bibliotek od nowa, więc budowanie jest szybsze.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Uczenie modeli ML podczas budowy obrazu: gotowe modele są częścią obrazu.
RUN python -m app.ml.train

# Serwer działa jako zwykły użytkownik, nie root (zasada najmniejszych uprawnień).
# Katalog /data przechowuje plik bazy SQLite i jest podpinany jako wolumen.
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

ENV DATABASE_URL=sqlite:////data/fitness_ai.db

EXPOSE 8000

# Przy starcie: wgranie atlasu ćwiczeń (pomija istniejące), potem serwer.
# Host 0.0.0.0 sprawia, że serwer jest dostępny spoza kontenera.
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
