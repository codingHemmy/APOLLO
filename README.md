# APOLLO RoboDrill Analytics

Eine moderne Ersatzplattform für das bestehende Python-FTP-Analyse-Tool. Das System besteht aus einem FastAPI-Backend und einer React/Vite-Oberfläche. Die Lösung erfüllt die Vorgaben aus dem Projektbrief (FTP-Pooling, Keyword-Extraktion, Charting, Dark/Light-Theme etc.).

## Features
- Paralleler FTP-Verbindungs-Pool mit MLSD/NLST-Fallback, Retry & NOOP-Healthcheck
- Analyse-Modi „Zeitraum“ und „Letzte X“, Keyword-basierte Messwert-Extraktion aus .DAT Dateien
- Maschinenlaufzeit-Heuristik laut Vorgabe, strukturierte Logs & Token-basierter Dateizugriff
- Live-Progress via Server-Sent Events, interaktive Diagramme (Zoom, Pan, Tooltips, Mittelwertlinie)
- Responsive Split-View UI mit RoboDrill-Auswahl, Keyword-Historie, Dark/Light-Theme und Statusbar
- Demo-Seeding-Skript für lokale FTP-Struktur, Integrationstests für Analysepfade
- Docker-Compose Setup (Frontend + Backend), Makefile für Dev-, Build- und Test-Workflows

## Schnellstart
1. **Konfiguration**
   ```bash
   cp .env.example .env
   ```
   Bei Bedarf Werte im Frontend unter „Settings“ (PUT /api/config) anpassen.

2. **Demo-Daten generieren (optional)**
   ```bash
   make seed
   ```
   Legt im Ordner `demo_ftp/` eine RoboDrill-Verzeichnisstruktur mit zufälligen .DAT-Dateien an.

3. **Lokaler Start (Entwicklung)**
   Backend:
   ```bash
   cd backend
   poetry install --no-root
   poetry run uvicorn app.main:app --reload
   ```
   Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Docker Compose**
   ```bash
   docker compose up --build
   ```
   Frontend: http://localhost:5173, Backend: http://localhost:8000

5. **Tests**
   ```bash
   make test
   ```

## Struktur
```
backend/
  app/                FastAPI-Anwendung inkl. FTP-Layer & Analyse-Services
  scripts/            Demo-Seeding Script
  tests/              Pytest-Integrationstests
frontend/
  src/                React + Vite UI
```

## Tastaturkürzel
- **Enter** in Keyword-Feld: startet Analyse (Browser-Standard)
- **ESC**: bricht laufende Analyse (Button „Abbrechen“)

## Sicherheit & Betrieb
- Basis-Authentifizierung optional über ENV (`SECURITY_BASIC_USER`, `SECURITY_BASIC_PASS`)
- Strikte Tokenisierung für Datei-Downloads, CORS nur für Frontend-Origin
- Strukturierte Logs via Python `logging`, Health Endpoint `/api/health`

## Bekannte Grenzen
- Externe FTP-Verbindung muss erreichbar sein oder via `demo_ftp` gemountet werden
- SSE-Antwort erfolgt über POST `/api/analyze` und erfordert Fetch-Streaming-Unterstützung im Browser
