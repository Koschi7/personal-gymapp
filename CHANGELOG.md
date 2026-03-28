# Changelog

Alle relevanten Änderungen an diesem Projekt werden hier dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
und dieses Projekt verwendet [Semantic Versioning](https://semver.org/lang/de/).

## [1.3.0] - 2026-03-28

### Hinzugefügt

- Übungs-Autocomplete: Beim Tippen werden bereits genutzte Übungen vorgeschlagen
- Autocomplete füllt automatisch das Körperteil-Dropdown aus
- Übungs-Statistik auf dem Dashboard mit Prozentanzeige und Zeitraum-Filtern
- Tappbare Kalendertage: Tap auf einen Trainingstag zeigt die Übungen des Tages
- Warnung beim Beenden eines Trainings ohne Übungen mit "Zurück" / "Trotzdem beenden"
- Leere Workouts werden beim Beenden automatisch verworfen (nicht gespeichert)

## [1.2.0] - 2026-03-28

### Hinzugefügt

- Trainingskalender auf dem Dashboard (Monatsansicht, Trainingstage als blaue Punkte, Heute hervorgehoben)
- Navigation zwischen Monaten im Kalender via HTMX
- Körperteil-Statistik mit Prozentanzeige (z.B. "67% Brust")
- Zeitraum-Filter für Statistiken: Heute, 7 Tage, 30 Tage, 90 Tage, Gesamt
- Datum beim Starten eines Trainings wählbar (für nachträgliches Eintragen)
- Fortschrittsbalken wird grün wenn Wochenziel/Monatsziel erreicht

### Geändert

- Dashboard-Layout komplett überarbeitet: Kalender + Goals + Stats + letztes Training
- Doughnut-Chart durch übersichtliche Balken mit Prozentanzeige ersetzt (stabiler auf Mobile)

## [1.1.0] - 2026-03-28

### Hinzugefügt

- Workout-Sessions: Training starten und beenden
- Körperteil-Tracking pro Übung (Brust, Rücken, Schulter, Nacken, Bauch, Beine)
- Statistik auf dem Dashboard: Balkendiagramm pro Körperteil
- Vergangene Trainings mit Körperteil-Tags in der Training-Ansicht
- Aktives Training auf dem Dashboard sichtbar mit "Beenden"-Button
- Körpergewicht-Eingabe im Profil (synchron mit Gewicht-Seite)

### Geändert

- Datumsformat auf DD.MM.YYYY (europäisch) umgestellt
- Monatsziel wird automatisch berechnet (Wochenziel x 4)
- Monatsziel-Eingabe im Profil entfernt
- "Training beenden"-Icon korrigiert

### Entfernt

- Separates Monatsziel-Feld in der Datenbank

## [1.0.0] - 2026-03-28

### Hinzugefügt

- Dashboard mit Begrüßung, Wochenziel, Monatsziel und letztem Training
- Training-Tracking: Übungen mit Name, Gewicht und Wiederholungen erfassen
- Übungen per HTMX hinzufügen und löschen (ohne Page Reload)
- Gewicht-Tracking mit Chart.js Verlaufsdiagramm
- Profil-Seite: Name, Profilbild, Trainingsziele konfigurierbar
- iOS-optimierte Bottom-Navigation (4 Tabs)
- Dark Mode als Standard (True Black OLED)
- Apple-inspiriertes UI mit Cards, Animationen und großen Tap-Targets
- Vollständig deutsche Benutzeroberfläche
- SQLite-Datenbank mit WAL-Modus
- Deployment-Konfiguration für Hetzner (systemd + Nginx)
- README mit Setup-Anleitung (lokal + Server)
