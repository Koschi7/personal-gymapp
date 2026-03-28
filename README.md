# GymApp

Persönliche Fitness-Tracking Web-App, optimiert für iPhone Safari. Minimalistisch, schnell, mit dunklem Apple-inspiriertem Design.

## Features

- **Workout-Sessions** — Training starten, Übungen erfassen, Training beenden
- **Körperteil-Tracking** — Jede Übung wird einem Körperteil zugeordnet (Brust, Rücken, Schulter, Nacken, Bauch, Beine)
- **Übungs-Autocomplete** — Bereits genutzte Übungen werden beim Tippen vorgeschlagen, inkl. automatischer Körperteil-Auswahl
- **Statistiken** — Körperteil- und Übungsverteilung mit Prozentanzeige, filterbar nach Zeitraum
- **Trainingskalender** — Monatsansicht mit Trainingstagen, Navigation zwischen Monaten, Tap auf einen Tag zeigt Details
- **Ziele** — Trainingstage pro Woche mit Fortschrittsbalken (Monat wird automatisch berechnet)
- **Gewicht verfolgen** — Körpergewicht-Verlauf mit Chart (auch im Profil eingebbar)
- **Personalisierung** — Name und Profilbild auf dem Dashboard
- **Nachträgliches Eintragen** — Datum beim Start eines Trainings wählbar
- **Leere Workouts** — Warnung beim Beenden ohne Übungen, Workout wird verworfen statt gespeichert

## Tech Stack

| Komponente | Technologie |
|---|---|
| Backend | Python 3.11+ / FastAPI |
| Storage | SQLite (WAL mode) |
| Frontend | Jinja2 Templates + HTMX |
| Chart | Chart.js (CDN) |
| Styling | Custom CSS (iOS-inspired) |

### Warum diese Entscheidungen?

- **FastAPI + Jinja2 + HTMX**: Kein Build-Step, kein JS-Framework, trotzdem schnelle partielle Updates. Perfekt für eine Single-User-App.
- **SQLite**: Null Konfiguration, eine Datei, WAL-Modus für gute Performance. Ideal für Einzelnutzer.
- **Chart.js via CDN**: Einzige externe JS-Dependency. Leichtgewichtig, gut dokumentiert.
- **Kein Auth**: Single-User-App — Zugriff wird über Netzwerk-Ebene gesteuert (VPN, Firewall).

## Setup

### Lokal

```bash
# Repository klonen
git clone <repo-url> && cd gymApp

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Starten
python main.py
# oder: uvicorn main:app --host 0.0.0.0 --port 8000
```

App öffnen: [http://localhost:8000](http://localhost:8000)

### Hetzner Server Deployment

#### 1. Server vorbereiten

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

#### 2. App deployen

```bash
sudo mkdir -p /opt/gymapp
sudo chown www-data:www-data /opt/gymapp

# Dateien kopieren (z.B. via scp oder git)
cd /opt/gymapp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. systemd Service einrichten

```bash
sudo cp deploy/gymapp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gymapp
sudo systemctl start gymapp
```

#### 4. Nginx konfigurieren

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gymapp
sudo ln -s /etc/nginx/sites-available/gymapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

#### 5. HTTPS (optional, empfohlen)

```bash
sudo certbot --nginx -d your-domain.de
```

#### Befehle

```bash
sudo systemctl status gymapp     # Status prüfen
sudo systemctl restart gymapp    # Neustarten
sudo journalctl -u gymapp -f     # Logs anzeigen
```

## Projektstruktur

```
gymApp/
├── main.py              # FastAPI App + Routen
├── database.py          # SQLite Schema + Queries
├── requirements.txt
├── data/                # DB + Uploads (nicht im Git)
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── training.html
│   ├── weight.html
│   ├── profile.html
│   └── partials/
│       ├── calendar.html
│       ├── current_exercises.html
│       ├── day_detail.html
│       ├── exercise_stats.html
│       ├── profile_form.html
│       ├── stats_section.html
│       └── weight_content.html
└── deploy/
    ├── gymapp.service
    └── nginx.conf
```

## Lizenz

Privates Projekt.
