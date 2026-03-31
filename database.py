import aiosqlite
import calendar
import os
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "gymapp.db"

BODY_PARTS = ["Brust", "Rücken", "Schulter", "Nacken", "Bauch", "Beine"]

GERMAN_MONTHS = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL DEFAULT '',
                picture TEXT DEFAULT NULL,
                goal_days_week INTEGER NOT NULL DEFAULT 4
            );

            INSERT OR IGNORE INTO profile (id, name) VALUES (1, '');

            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                ended_at TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                body_part TEXT NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS weight_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weight REAL NOT NULL,
                date TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_exercises_workout ON exercises(workout_id);
            CREATE INDEX IF NOT EXISTS idx_exercises_body_part ON exercises(body_part);
            CREATE INDEX IF NOT EXISTS idx_workouts_started ON workouts(started_at);
            CREATE INDEX IF NOT EXISTS idx_weight_date ON weight_log(date);
        """)

        # Migration: add set_number column if missing
        cursor = await db.execute("PRAGMA table_info(exercises)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "set_number" not in columns:
            await db.execute("ALTER TABLE exercises ADD COLUMN set_number INTEGER NOT NULL DEFAULT 1")

        await db.commit()
    finally:
        await db.close()


def format_date(iso_str: str) -> str:
    """Convert 'YYYY-MM-DD ...' to 'DD.MM.YYYY'."""
    try:
        d = datetime.fromisoformat(iso_str[:10])
        return d.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return iso_str


def format_datetime(iso_str: str) -> str:
    """Convert 'YYYY-MM-DD HH:MM:SS' to 'DD.MM.YYYY, HH:MM'."""
    try:
        d = datetime.fromisoformat(iso_str)
        return d.strftime("%d.%m.%Y, %H:%M")
    except (ValueError, TypeError):
        return iso_str


# --- Profile ---

async def get_profile() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM profile WHERE id = 1")
        row = await cursor.fetchone()
        p = dict(row) if row else {"id": 1, "name": "", "picture": None, "goal_days_week": 4}
        p["goal_days_month"] = p["goal_days_week"] * 4
        return p
    finally:
        await db.close()


async def update_profile(name: str | None = None, picture: str | None = None,
                         goal_days_week: int | None = None):
    db = await get_db()
    try:
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if picture is not None:
            updates.append("picture = ?")
            values.append(picture)
        if goal_days_week is not None:
            updates.append("goal_days_week = ?")
            values.append(goal_days_week)
        if updates:
            await db.execute(f"UPDATE profile SET {', '.join(updates)} WHERE id = 1", values)
            await db.commit()
    finally:
        await db.close()


def group_exercises(exercises: list[dict]) -> list[dict]:
    """Group exercises by name, preserving insertion order."""
    groups = {}
    order = []
    for ex in exercises:
        if ex["name"] not in groups:
            order.append(ex["name"])
            groups[ex["name"]] = {"name": ex["name"], "body_part": ex["body_part"], "sets": []}
        groups[ex["name"]]["sets"].append(ex)
    return [groups[name] for name in order]


# --- Workouts ---

async def start_workout(custom_date: str | None = None) -> dict:
    db = await get_db()
    try:
        if custom_date:
            started = f"{custom_date} {datetime.now().strftime('%H:%M:%S')}"
            cursor = await db.execute(
                "INSERT INTO workouts (started_at) VALUES (?)", (started,)
            )
        else:
            cursor = await db.execute("INSERT INTO workouts DEFAULT VALUES")
        await db.commit()
        row_cursor = await db.execute("SELECT * FROM workouts WHERE id = ?", (cursor.lastrowid,))
        row = await row_cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def end_workout(workout_id: int):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE workouts SET ended_at = datetime('now', 'localtime') WHERE id = ?",
            (workout_id,)
        )
        await db.commit()
    finally:
        await db.close()


async def get_active_workout() -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workouts WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_past_workouts(limit: int = 20) -> list[dict]:
    """Get completed workouts with their exercises."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workouts WHERE ended_at IS NOT NULL ORDER BY started_at DESC LIMIT ?",
            (limit,)
        )
        workouts = [dict(r) for r in await cursor.fetchall()]
        for w in workouts:
            ex_cursor = await db.execute(
                "SELECT * FROM exercises WHERE workout_id = ? ORDER BY created_at",
                (w["id"],)
            )
            w["exercises"] = [dict(r) for r in await ex_cursor.fetchall()]
            w["exercise_groups"] = group_exercises(w["exercises"])
            w["body_parts"] = sorted(set(e["body_part"] for e in w["exercises"]))
            w["started_fmt"] = format_datetime(w["started_at"])
            w["date_fmt"] = format_date(w["started_at"])
        return workouts
    finally:
        await db.close()


async def get_workouts_for_date(iso_date: str) -> list[dict]:
    """Get all completed workouts for a specific date with exercises."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workouts WHERE ended_at IS NOT NULL AND date(started_at) = ? ORDER BY started_at",
            (iso_date,)
        )
        workouts = [dict(r) for r in await cursor.fetchall()]
        for w in workouts:
            ex_cursor = await db.execute(
                "SELECT * FROM exercises WHERE workout_id = ? ORDER BY created_at",
                (w["id"],)
            )
            w["exercises"] = [dict(r) for r in await ex_cursor.fetchall()]
            w["exercise_groups"] = group_exercises(w["exercises"])
            w["body_parts"] = sorted(set(e["body_part"] for e in w["exercises"]))
            w["started_fmt"] = format_datetime(w["started_at"])
            w["date_fmt"] = format_date(w["started_at"])
        return workouts
    finally:
        await db.close()


async def delete_workout(workout_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
        await db.commit()
    finally:
        await db.close()


# --- Exercises ---

async def add_exercise(workout_id: int, name: str, body_part: str, weight: float, reps: int) -> dict:
    db = await get_db()
    try:
        # Auto-calculate set number
        cnt_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM exercises WHERE workout_id = ? AND name = ?",
            (workout_id, name)
        )
        cnt_row = await cnt_cursor.fetchone()
        set_number = (cnt_row["cnt"] if cnt_row else 0) + 1

        cursor = await db.execute(
            "INSERT INTO exercises (workout_id, name, body_part, weight, reps, set_number) VALUES (?, ?, ?, ?, ?, ?)",
            (workout_id, name, body_part, weight, reps, set_number)
        )
        await db.commit()
        row_cursor = await db.execute("SELECT * FROM exercises WHERE id = ?", (cursor.lastrowid,))
        row = await row_cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def get_workout_exercises(workout_id: int) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM exercises WHERE workout_id = ? ORDER BY created_at ASC",
            (workout_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def search_exercise_names(query: str, limit: int = 8) -> list[dict]:
    """Search distinct exercise names matching a prefix, with their last used body_part."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT e.name, e.body_part, MAX(e.created_at) as last_used
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL AND e.name LIKE ? || '%'
            GROUP BY e.name
            ORDER BY last_used DESC
            LIMIT ?
        """, (query, limit))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_exercise_stats_filtered(period: str = "all") -> list[dict]:
    """Get exercise name stats with counts for a given time period."""
    date_filter = ""
    if period == "today":
        date_filter = "AND date(w.started_at) = date('now', 'localtime')"
    elif period == "7days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-7 days')"
    elif period == "30days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-30 days')"
    elif period == "90days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-90 days')"

    db = await get_db()
    try:
        cursor = await db.execute(f"""
            SELECT e.name, e.body_part, COUNT(*) as count,
                   SUM(e.weight * e.reps) as volume
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL {date_filter}
            GROUP BY e.name
            ORDER BY count DESC
            LIMIT 15
        """)
        rows = [dict(r) for r in await cursor.fetchall()]
        total = sum(r["count"] for r in rows)
        for r in rows:
            r["pct"] = round(r["count"] / total * 100) if total > 0 else 0
        return rows
    finally:
        await db.close()


async def get_max_weight(exercise_name: str) -> float | None:
    """Get the all-time max weight for an exercise (from completed workouts only)."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT MAX(e.weight) as max_weight FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL AND e.name = ?
        """, (exercise_name,))
        row = await cursor.fetchone()
        return row["max_weight"] if row and row["max_weight"] is not None else None
    finally:
        await db.close()


async def get_personal_records(limit: int = 10) -> list[dict]:
    """Get top PRs (max weight per exercise) from completed workouts."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT e.name, e.body_part, MAX(e.weight) as max_weight, MAX(e.reps) as best_reps
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL
            GROUP BY e.name
            ORDER BY max_weight DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_exercise_history(exercise_name: str) -> list[dict]:
    """Get weight/volume history for an exercise over time, grouped by workout date."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT date(w.started_at) as date, MAX(e.weight) as max_weight,
                   SUM(e.weight * e.reps) as volume, SUM(e.reps) as total_reps,
                   COUNT(*) as sets
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL AND e.name = ?
            GROUP BY date(w.started_at)
            ORDER BY date(w.started_at) ASC
        """, (exercise_name,))
        rows = await cursor.fetchall()
        result = [dict(r) for r in rows]
        for entry in result:
            entry["date_fmt"] = format_date(entry["date"])
        return result
    finally:
        await db.close()


async def get_last_performance(exercise_name: str) -> list[dict]:
    """Get weight/reps from the most recent completed workout containing this exercise."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT e.weight, e.reps FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL AND e.name = ?
            AND w.id = (
                SELECT w2.id FROM workouts w2
                JOIN exercises e2 ON e2.workout_id = w2.id
                WHERE w2.ended_at IS NOT NULL AND e2.name = ?
                ORDER BY w2.started_at DESC LIMIT 1
            )
            ORDER BY e.created_at
        """, (exercise_name, exercise_name))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def delete_exercise(exercise_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        await db.commit()
    finally:
        await db.close()


# --- Stats ---

async def get_training_days_week() -> int:
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT COUNT(DISTINCT date(started_at)) as days
            FROM workouts
            WHERE ended_at IS NOT NULL
              AND date(started_at) >= date('now', 'localtime', 'weekday 1', '-7 days')
              AND date(started_at) <= date('now', 'localtime')
        """)
        row = await cursor.fetchone()
        return row["days"] if row else 0
    finally:
        await db.close()


async def get_training_days_month() -> int:
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT COUNT(DISTINCT date(started_at)) as days
            FROM workouts
            WHERE ended_at IS NOT NULL
              AND strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now', 'localtime')
        """)
        row = await cursor.fetchone()
        return row["days"] if row else 0
    finally:
        await db.close()


async def get_body_part_stats_filtered(period: str = "all") -> list[dict]:
    """Get body part stats with percentages for a given time period.

    period: 'today', '7days', '30days', '90days', 'all'
    """
    date_filter = ""
    if period == "today":
        date_filter = "AND date(w.started_at) = date('now', 'localtime')"
    elif period == "7days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-7 days')"
    elif period == "30days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-30 days')"
    elif period == "90days":
        date_filter = "AND date(w.started_at) >= date('now', 'localtime', '-90 days')"

    db = await get_db()
    try:
        cursor = await db.execute(f"""
            SELECT e.body_part, COUNT(*) as count
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.ended_at IS NOT NULL {date_filter}
            GROUP BY e.body_part
            ORDER BY count DESC
        """)
        rows = [dict(r) for r in await cursor.fetchall()]
        total = sum(r["count"] for r in rows)
        for r in rows:
            r["pct"] = round(r["count"] / total * 100) if total > 0 else 0
        return rows
    finally:
        await db.close()


async def get_last_workout() -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workouts WHERE ended_at IS NOT NULL ORDER BY started_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        if not row:
            return None
        w = dict(row)
        ex_cursor = await db.execute(
            "SELECT * FROM exercises WHERE workout_id = ? ORDER BY created_at",
            (w["id"],)
        )
        w["exercises"] = [dict(r) for r in await ex_cursor.fetchall()]
        w["exercise_groups"] = group_exercises(w["exercises"])
        w["body_parts"] = sorted(set(e["body_part"] for e in w["exercises"]))
        w["date_fmt"] = format_date(w["started_at"])
        return w
    finally:
        await db.close()


# --- Calendar ---

async def get_calendar_data(year: int, month: int) -> dict:
    """Build calendar grid for a given month with training day markers."""
    db = await get_db()
    try:
        month_str = f"{year:04d}-{month:02d}"
        cursor = await db.execute("""
            SELECT date(started_at) as d,
                   GROUP_CONCAT(DISTINCT (SELECT e.body_part FROM exercises e WHERE e.workout_id = w.id)) as parts
            FROM workouts w
            WHERE w.ended_at IS NOT NULL
              AND strftime('%Y-%m', w.started_at) = ?
            GROUP BY date(started_at)
        """, (month_str,))
        rows = await cursor.fetchall()
        training_days = {}
        for r in rows:
            day_num = int(r["d"].split("-")[2])
            training_days[day_num] = (r["parts"] or "").split(",")

        # Build weeks grid (Mon=0)
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(year, month)

        today = date.today()
        today_day = today.day if today.year == year and today.month == month else None

        # Training days count for this month
        training_count = len(training_days)

        # Prev/next month
        if month == 1:
            prev_y, prev_m = year - 1, 12
        else:
            prev_y, prev_m = year, month - 1
        if month == 12:
            next_y, next_m = year + 1, 1
        else:
            next_y, next_m = year, month + 1

        return {
            "year": year,
            "month": month,
            "month_name": GERMAN_MONTHS[month],
            "weeks": weeks,
            "training_days": training_days,
            "today_day": today_day,
            "training_count": training_count,
            "prev_year": prev_y,
            "prev_month": prev_m,
            "next_year": next_y,
            "next_month": next_m,
        }
    finally:
        await db.close()


# --- Weight Log ---

async def add_weight(weight: float, log_date: str | None = None) -> dict:
    if log_date is None:
        log_date = date.today().isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO weight_log (weight, date) VALUES (?, ?)",
            (weight, log_date)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM weight_log WHERE date = ?", (log_date,))
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def get_weight_history(limit: int = 30) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM weight_log ORDER BY date DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        result = [dict(r) for r in rows]
        for entry in result:
            entry["date_fmt"] = format_date(entry["date"])
        return result
    finally:
        await db.close()


async def delete_weight(weight_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM weight_log WHERE id = ?", (weight_id,))
        await db.commit()
    finally:
        await db.close()
