# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.3.1] - 2026-03-28

### Changed

- Rewrote README in English for public repository
- Generalized deployment guide (no longer vendor-specific)
- Added deployment options for Railway, Render, Fly.io, Tailscale, Docker
- Added localization section explaining how to translate the German UI
- Added MIT license
- Translated CHANGELOG to English

## [1.3.0] - 2026-03-28

### Added

- Exercise autocomplete: previously used exercises are suggested as you type
- Autocomplete auto-fills the body part dropdown
- Exercise statistics on dashboard with percentages and time range filters
- Tappable calendar days: tap a training day to see the full workout details
- Warning when ending a workout without exercises ("Go back" / "End anyway")
- Empty workouts are automatically discarded (not saved)

## [1.2.0] - 2026-03-28

### Added

- Training calendar on dashboard (monthly view, blue dots for training days, today highlighted)
- Month navigation in calendar via HTMX
- Body part statistics with percentage display (e.g. "67% Chest")
- Time range filters for stats: Today, 7 days, 30 days, 90 days, All time
- Date picker when starting a workout (for backdating)
- Progress bars turn green when weekly/monthly goal is reached

### Changed

- Completely redesigned dashboard layout: calendar + goals + stats + last workout
- Replaced doughnut chart with horizontal bars + percentages (more stable on mobile)

## [1.1.0] - 2026-03-28

### Added

- Workout sessions: start and end training
- Body part tracking per exercise (Brust, Rücken, Schulter, Nacken, Bauch, Beine)
- Body part bar chart on dashboard
- Past workouts with body part tags in training view
- Active workout visible on dashboard with "End" button
- Bodyweight input on profile page (synced with weight page)

### Changed

- Date format switched to DD.MM.YYYY (European)
- Monthly goal auto-calculated from weekly goal (x4)
- Removed separate monthly goal input from profile
- Fixed "end training" icon rendering

### Removed

- Separate monthly goal field in database

## [1.0.0] - 2026-03-28

### Added

- Dashboard with greeting, weekly/monthly goals, and last workout
- Exercise tracking with name, weight, and reps
- Add/delete exercises via HTMX (no page reload)
- Bodyweight tracking with Chart.js line graph
- Profile page: name, photo, training goals
- iOS-style bottom tab navigation (4 tabs)
- Dark mode by default (true black for OLED)
- Apple-inspired UI with cards, animations, and large tap targets
- Fully German user interface
- SQLite database with WAL mode
- Deployment config (systemd + nginx)
- README with local + server setup guide
