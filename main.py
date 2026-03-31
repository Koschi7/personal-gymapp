import os
import shutil
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database as db

UPLOAD_DIR = Path(__file__).parent / "data" / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


# --- Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    profile = await db.get_profile()
    days_week = await db.get_training_days_week()
    days_month = await db.get_training_days_month()
    last_workout = await db.get_last_workout()
    body_part_stats = await db.get_body_part_stats_filtered("all")
    exercise_stats = await db.get_exercise_stats_filtered("all")
    active_workout = await db.get_active_workout()
    active_exercises = []
    if active_workout:
        active_exercises = await db.get_workout_exercises(active_workout["id"])
        active_workout["started_fmt"] = db.format_datetime(active_workout["started_at"])
    personal_records = await db.get_personal_records()
    today = date.today()
    cal = await db.get_calendar_data(today.year, today.month)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "profile": profile,
        "days_week": days_week,
        "days_month": days_month,
        "last_workout": last_workout,
        "body_part_stats": body_part_stats,
        "exercise_stats": exercise_stats,
        "active_workout": active_workout,
        "active_exercises": active_exercises,
        "personal_records": personal_records,
        "cal": cal,
        "active_period": "all",
        "active": "dashboard",
    })


# --- Calendar HTMX ---

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_partial(request: Request, year: int = Query(...), month: int = Query(...)):
    profile = await db.get_profile()
    cal = await db.get_calendar_data(year, month)
    return templates.TemplateResponse("partials/calendar.html", {
        "request": request,
        "cal": cal,
        "profile": profile,
    })


# --- Day Detail HTMX ---

@app.get("/day/{iso_date}", response_class=HTMLResponse)
async def day_detail(request: Request, iso_date: str):
    workouts = await db.get_workouts_for_date(iso_date)
    return templates.TemplateResponse("partials/day_detail.html", {
        "request": request,
        "workouts": workouts,
        "date_fmt": db.format_date(iso_date),
    })


# --- Exercise Autocomplete ---

@app.get("/exercises/search")
async def exercise_search(q: str = Query("")):
    if len(q) < 1:
        return []
    results = await db.search_exercise_names(q)
    return [{"name": r["name"], "body_part": r["body_part"]} for r in results]


@app.get("/exercises/last", response_class=HTMLResponse)
async def exercise_last_performance(request: Request, name: str = Query("")):
    if not name.strip():
        return HTMLResponse("")
    sets = await db.get_last_performance(name.strip())
    if not sets:
        return HTMLResponse("")
    return templates.TemplateResponse("partials/last_performance.html", {
        "request": request,
        "sets": sets,
    })


# --- Exercise Stats HTMX ---

@app.get("/exercise-stats", response_class=HTMLResponse)
async def exercise_stats_partial(request: Request, period: str = Query("all")):
    exercise_stats = await db.get_exercise_stats_filtered(period)
    return templates.TemplateResponse("partials/exercise_stats.html", {
        "request": request,
        "exercise_stats": exercise_stats,
        "active_period": period,
    })


# --- Stats HTMX ---

@app.get("/stats", response_class=HTMLResponse)
async def stats_partial(request: Request, period: str = Query("all")):
    body_part_stats = await db.get_body_part_stats_filtered(period)
    return templates.TemplateResponse("partials/stats_section.html", {
        "request": request,
        "body_part_stats": body_part_stats,
        "active_period": period,
    })


# --- Training ---

@app.get("/training", response_class=HTMLResponse)
async def training_page(request: Request):
    active_workout = await db.get_active_workout()
    exercises = []
    if active_workout:
        exercises = await db.get_workout_exercises(active_workout["id"])
    past_workouts = await db.get_past_workouts()
    return templates.TemplateResponse("training.html", {
        "request": request,
        "active_workout": active_workout,
        "exercises": exercises,
        "exercise_groups": db.group_exercises(exercises),
        "past_workouts": past_workouts,
        "body_parts": db.BODY_PARTS,
        "today": date.today().isoformat(),
        "active": "training",
    })


@app.post("/training/start", response_class=HTMLResponse)
async def start_workout(request: Request, workout_date: str = Form("")):
    custom_date = workout_date if workout_date else None
    await db.start_workout(custom_date=custom_date)
    return RedirectResponse("/training", status_code=303)


@app.post("/training/end/{workout_id}", response_class=HTMLResponse)
async def end_workout(request: Request, workout_id: int):
    exercises = await db.get_workout_exercises(workout_id)
    if not exercises:
        # No exercises — discard the workout entirely
        await db.delete_workout(workout_id)
    else:
        await db.end_workout(workout_id)
    referer = request.headers.get("referer", "/training")
    if "/" == referer.rstrip("/").split("/")[-1] or referer.endswith(":8000") or referer.endswith(":8000/"):
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/training", status_code=303)


@app.post("/training/add", response_class=HTMLResponse)
async def add_exercise(
    request: Request,
    workout_id: int = Form(...),
    name: str = Form(...),
    body_part: str = Form(...),
    weight: float = Form(...),
    reps: int = Form(...),
):
    # Check for PR before adding (so we compare against previous max)
    prev_max = await db.get_max_weight(name)
    is_pr = prev_max is not None and weight > prev_max

    await db.add_exercise(workout_id, name, body_part, weight, reps)
    if is_htmx(request):
        exercises = await db.get_workout_exercises(workout_id)
        return templates.TemplateResponse("partials/current_exercises.html", {
            "request": request,
            "exercises": exercises,
            "exercise_groups": db.group_exercises(exercises),
            "new_pr": {"name": name, "weight": weight} if is_pr else None,
        })
    return RedirectResponse("/training", status_code=303)


@app.delete("/training/exercise/{exercise_id}", response_class=HTMLResponse)
async def remove_exercise(request: Request, exercise_id: int, workout_id: int = 0):
    await db.delete_exercise(exercise_id)
    if is_htmx(request) and workout_id:
        exercises = await db.get_workout_exercises(workout_id)
        return templates.TemplateResponse("partials/current_exercises.html", {
            "request": request,
            "exercises": exercises,
            "exercise_groups": db.group_exercises(exercises),
        })
    return RedirectResponse("/training", status_code=303)


@app.delete("/training/workout/{workout_id}", response_class=HTMLResponse)
async def remove_workout(request: Request, workout_id: int):
    await db.delete_workout(workout_id)
    return RedirectResponse("/training", status_code=303)


# --- Weight ---

@app.get("/weight", response_class=HTMLResponse)
async def weight_page(request: Request):
    history = await db.get_weight_history()
    return templates.TemplateResponse("weight.html", {
        "request": request,
        "history": history,
        "active": "weight",
    })


@app.post("/weight", response_class=HTMLResponse)
async def add_weight_entry(request: Request, weight: float = Form(...)):
    await db.add_weight(weight)
    if is_htmx(request):
        history = await db.get_weight_history()
        return templates.TemplateResponse("partials/weight_content.html", {
            "request": request,
            "history": history,
        })
    return RedirectResponse("/weight", status_code=303)


@app.delete("/weight/{weight_id}", response_class=HTMLResponse)
async def remove_weight(request: Request, weight_id: int):
    await db.delete_weight(weight_id)
    if is_htmx(request):
        history = await db.get_weight_history()
        return templates.TemplateResponse("partials/weight_content.html", {
            "request": request,
            "history": history,
        })
    return RedirectResponse("/weight", status_code=303)


# --- Profile ---

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    profile = await db.get_profile()
    weight_history = await db.get_weight_history(limit=1)
    current_weight = weight_history[0]["weight"] if weight_history else None
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": profile,
        "current_weight": current_weight,
        "active": "profile",
    })


@app.post("/profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    name: str = Form(""),
    goal_days_week: int = Form(4),
    current_weight: str = Form(""),
    picture: UploadFile | None = File(None),
):
    picture_path = None
    if picture and picture.filename:
        ext = Path(picture.filename).suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            filename = f"profile{ext}"
            filepath = UPLOAD_DIR / filename
            with open(filepath, "wb") as f:
                shutil.copyfileobj(picture.file, f)
            picture_path = filename

    await db.update_profile(
        name=name,
        picture=picture_path,
        goal_days_week=goal_days_week,
    )

    if current_weight.strip():
        try:
            await db.add_weight(float(current_weight))
        except ValueError:
            pass

    if is_htmx(request):
        profile = await db.get_profile()
        weight_history = await db.get_weight_history(limit=1)
        cw = weight_history[0]["weight"] if weight_history else None
        return templates.TemplateResponse("partials/profile_form.html", {
            "request": request,
            "profile": profile,
            "current_weight": cw,
            "saved": True,
        })
    return RedirectResponse("/profile", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
