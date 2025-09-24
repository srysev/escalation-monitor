# api/app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.storage import get_today_report
from src.scoring import ESLALATION_SCALA
from datetime import datetime, timezone

app = FastAPI(title="Escalation Monitor API")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Server-rendered dashboard with current escalation data."""
    # Heutigen Report laden
    report = get_today_report()

    # Skala parsen
    scale_lines = ESLALATION_SCALA.strip().split('\n')
    scale_levels = []
    for line in scale_lines:
        if '=' in line and ':' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                num = parts[0].strip()
                rest = parts[1].split(':', 1)
                if len(rest) == 2:
                    label = rest[0].strip()
                    desc = rest[1].strip()
                    try:
                        scale_levels.append({
                            "number": int(num),
                            "label": label,
                            "description": desc
                        })
                    except ValueError:
                        pass

    # Timestamp formatieren
    if report and "timestamp" in report:
        try:
            dt = datetime.fromisoformat(report["timestamp"].replace('Z', '+00:00'))
            formatted_timestamp = dt.strftime("%d.%m.%Y, %H:%M Uhr")
        except:
            formatted_timestamp = "Unbekannt"
    else:
        formatted_timestamp = "Keine Daten"

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "report": report,
            "scale_levels": scale_levels,
            "formatted_timestamp": formatted_timestamp
        }
    )

@app.get("/score")
def score():
    report = get_today_report()
    if report and "escalation_result" in report:
        return {"score": report["escalation_result"].get("score", 1.0)}
    return {"score": 1.0}

@app.get("/metrics")
def metrics():
    report = get_today_report()
    if report and "escalation_result" in report:
        return JSONResponse(report["escalation_result"])
    return JSONResponse({"error": "No data available"})