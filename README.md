# GymApp

A minimal, self-hosted fitness tracking web app built for daily use on your phone. Dark, fast, no bloat.

Built with **FastAPI + SQLite + Jinja2 + HTMX** — no JavaScript framework, no build step, no account needed.

> **Note:** The UI is entirely in **German** (Deutsch). All strings live in Jinja2 templates and are easy to translate — see [Localization](#localization).

## Why

Most fitness apps are overloaded with features, require sign-ups, track you, or cost money. This is a personal tool: one user, one server, full control. Deploy it on any VPS or run it locally.

## Features

- **Workout sessions** — Start a workout, log exercises, end it. Backdate to any day.
- **Body part tracking** — Every exercise maps to a body part (Brust, Rücken, Schulter, Nacken, Bauch, Beine)
- **Exercise autocomplete** — Previously used exercises are suggested as you type, auto-filling the body part
- **Statistics** — Body part and exercise distribution with percentages, filterable by time range (today, 7/30/90 days, all time)
- **Training calendar** — Monthly view with training day dots. Tap a day to see the full workout.
- **Weekly/monthly goals** — Set a weekly target, monthly is calculated automatically. Progress bars turn green when hit.
- **Bodyweight tracking** — Manual input with a Chart.js line graph
- **Profile** — Name, photo, weight, and goal settings
- **Empty workout protection** — Warning before discarding a workout with no exercises

## Screenshots

> TODO: Add screenshots of the iPhone UI

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11+ / FastAPI |
| Storage | SQLite (WAL mode) |
| Frontend | Jinja2 Templates + HTMX |
| Chart | Chart.js (CDN) |
| Styling | Custom CSS (iOS-inspired dark theme) |

### Design decisions

- **No JS framework** — Jinja2 renders HTML on the server, HTMX handles partial updates. Zero build step, instant deploys.
- **SQLite** — Single file, zero config, WAL mode for performance. Perfect for single-user.
- **No auth** — This is a personal app. Restrict access at the network level (VPN, firewall, Tailscale, etc.).
- **HTMX everywhere** — Adding exercises, switching stats filters, navigating the calendar — all without full page reloads.

## Quick Start

```bash
git clone https://github.com/Koschi7/personal-gymapp.git
cd personal-gymapp

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py
```

Open [http://localhost:8000](http://localhost:8000) on your phone (same WiFi) or browser.

## Configuration

The app runs on `0.0.0.0:8000` by default. To change host/port, edit the last lines of `main.py` or run:

```bash
uvicorn main:app --host 0.0.0.0 --port 3000
```

Data is stored in `data/gymapp.db` (auto-created on first run). Back up this file to preserve your data.

## Deployment

The app is a single Python process serving on a port. Any deployment method that can run a Python app works.

### General steps

1. Copy the project to your server
2. Create a virtual environment and install dependencies
3. Run with a process manager (systemd, supervisor, pm2, etc.)
4. Put a reverse proxy in front (nginx, caddy, traefik, etc.)

### Example: systemd + nginx (any Linux VPS)

#### systemd service

```bash
sudo cp deploy/gymapp.service /etc/systemd/system/
# Edit the service file to match your paths and user
sudo systemctl daemon-reload
sudo systemctl enable gymapp
sudo systemctl start gymapp
```

#### nginx reverse proxy

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gymapp
# Edit server_name to your domain
sudo ln -s /etc/nginx/sites-available/gymapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### HTTPS

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Example: Docker (coming soon)

### Other options

- **Railway / Render / Fly.io** — Push and deploy, set start command to `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Tailscale** — Run locally, access from anywhere without exposing to the internet
- **Home server** — Run on a Raspberry Pi or NAS on your local network

### Useful commands

```bash
sudo systemctl status gymapp     # Check status
sudo systemctl restart gymapp    # Restart
sudo journalctl -u gymapp -f     # View logs
```

## Project Structure

```
personal-gymapp/
├── main.py              # FastAPI app + all routes
├── database.py          # SQLite schema + query functions
├── requirements.txt     # 5 dependencies
├── data/                # SQLite DB + uploads (gitignored)
├── static/
│   └── style.css        # iOS-inspired dark theme
├── templates/
│   ├── base.html        # Layout + bottom tab bar
│   ├── dashboard.html   # Home screen
│   ├── training.html    # Workout session + history
│   ├── weight.html      # Bodyweight tracker + chart
│   ├── profile.html     # Settings
│   └── partials/        # HTMX partial templates
└── deploy/
    ├── gymapp.service   # systemd unit file
    └── nginx.conf       # nginx reverse proxy config
```

## Localization

The UI is currently in German. All user-facing strings are in the Jinja2 templates (`templates/`). To translate:

1. Search for German text in `templates/*.html` and `templates/partials/*.html`
2. Replace with your language
3. Update `BODY_PARTS` in `database.py`

No i18n framework needed — it's just HTML.

## Built With

This project was built collaboratively with [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding agent). Architecture, implementation, and iteration were done in a back-and-forth conversation — from initial concept to deployed app.

## License

MIT — see [LICENSE](LICENSE).
