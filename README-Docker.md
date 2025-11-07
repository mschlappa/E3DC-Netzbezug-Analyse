# Netzbezug Analyse App - Docker Installation

Diese Anleitung zeigt Ihnen, wie Sie die Netzbezug Analyse App mit Docker starten.

## Voraussetzungen

- Docker Desktop installiert (enthält Docker und Docker Compose)
  - Windows/Mac: https://www.docker.com/products/docker-desktop
  - Linux: `sudo apt-get install docker.io docker-compose`

## Installation und Start

### Option 1: Mit Docker Compose (Empfohlen)

Docker Compose startet automatisch die App und eine PostgreSQL-Datenbank.

```bash
# Container bauen und starten
docker-compose up -d

# App ist verfügbar unter: http://localhost:5000
```

### Option 2: Nur die App (mit externer Datenbank)

Falls Sie bereits eine PostgreSQL-Datenbank haben:

```bash
# Docker Image bauen
docker build -t netzbezug-app .

# Container starten (passen Sie die DATABASE_URL an)
docker run -d \
  -p 5000:5000 \
  -e DATABASE_URL="postgresql://username:password@host:5432/dbname" \
  --name netzbezug-app \
  netzbezug-app
```

## Verwaltung

### Logs anzeigen
```bash
# Alle Logs
docker-compose logs -f

# Nur App-Logs
docker-compose logs -f app

# Nur Datenbank-Logs
docker-compose logs -f db
```

### Container stoppen
```bash
docker-compose down
```

### Container stoppen und Daten löschen
```bash
docker-compose down -v
```

### Container neu starten
```bash
docker-compose restart
```

### Container neu bauen (nach Code-Änderungen)
```bash
docker-compose up -d --build
```

## Zugriff

- **Web-App**: http://localhost:5000
- **PostgreSQL**: localhost:5432
  - Benutzer: `netzbezug_user`
  - Passwort: `netzbezug_password`
  - Datenbank: `netzbezug_db`

## Sicherheitshinweis

Die Standard-Passwörter in `docker-compose.yml` sind NUR für lokale Entwicklung geeignet!

Für Produktiv-Systeme ändern Sie bitte:
1. `POSTGRES_PASSWORD` in der docker-compose.yml
2. Die `DATABASE_URL` entsprechend anpassen

## Daten-Persistenz

Die Datenbank-Daten werden im Docker Volume `postgres_data` gespeichert und bleiben erhalten, auch wenn Sie die Container stoppen.

## Fehlerbehebung

### Port 5000 bereits belegt
Ändern Sie in `docker-compose.yml` die Port-Zuordnung von `5000:5000` zu `8080:5000` (oder einen anderen freien Port).

### Chromium-Fehler beim PDF-Export
Dies sollte nicht auftreten, da Chromium im Docker-Image enthalten ist. Falls doch:
```bash
docker-compose logs app
```

### Datenbank-Verbindungsfehler
Prüfen Sie, ob die Datenbank bereit ist:
```bash
docker-compose ps
```

Beide Services sollten "Up" und "healthy" sein.
