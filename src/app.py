# src/app.py
import os
import hashlib
import secrets
from urllib.parse import quote
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.storage import get_today_report
from src.agents.review import ESKALATIONSSKALA
from datetime import datetime, timezone

app = FastAPI(title="Escalation Monitor API")
templates = Jinja2Templates(directory="src/templates")

# --- Auth Configuration ---
EXPECTED_TOKEN = None
COOKIE_SECRET = None

def get_cookie_secret():
    global COOKIE_SECRET
    if COOKIE_SECRET is None:
        COOKIE_SECRET = os.getenv("COOKIE_SECRET", secrets.token_hex(32))
    return COOKIE_SECRET

def create_secure_token(password: str) -> str:
    secret = get_cookie_secret()
    return hashlib.sha256(f"{password}:{secret}".encode()).hexdigest()

def get_expected_token():
    global EXPECTED_TOKEN
    if EXPECTED_TOKEN is None:
        password = os.getenv("DASHBOARD_PASSWORD")
        if password:
            EXPECTED_TOKEN = create_secure_token(password)
    return EXPECTED_TOKEN

# --- Auth Middleware ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Check if authentication is enabled
    dashboard_password = os.getenv("DASHBOARD_PASSWORD")

    # If no DASHBOARD_PASSWORD is set, skip authentication
    if not dashboard_password:
        response = await call_next(request)
        return response

    # Define public paths that don't require authentication
    public_paths = ["/login", "/auth/login"]
    public_static_extensions = [".css", ".js", ".png", ".ico", ".svg", ".html"]

    # Check if current path is public
    path = request.url.path
    if (path in public_paths or
        any(path.endswith(ext) for ext in public_static_extensions) or
        path.startswith("/public/")):
        response = await call_next(request)
        return response

    # Check web authentication (cookies)
    auth_token = request.cookies.get("auth_token")
    expected_token = get_expected_token()
    web_auth_valid = auth_token and expected_token and auth_token == expected_token

    if not web_auth_valid:
        # Redirect to login page with return URL
        return RedirectResponse(
            url=f"/login?redirect={request.url.path}",
            status_code=302
        )

    # Authentication successful, proceed with request
    response = await call_next(request)
    return response

# deactivated because Vercel says: app.mount("/public", ...) is not needed and should not be used. ---Mount static files for serving login.html
#app.mount("/public", StaticFiles(directory="public"), name="public")

# --- Login Routes ---
class LoginRequest(BaseModel):
    password: str
    redirect: str = "/"

@app.get("/login")
async def login_page(request: Request):
    """Redirect to static login page with redirect parameter."""
    redirect_target = request.query_params.get("redirect")
    if redirect_target:
        safe_target = quote(redirect_target, safe="/")
        return RedirectResponse(f"/login.html?redirect={safe_target}", status_code=307)
    return RedirectResponse("/login.html", status_code=307)

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and set secure cookie."""
    dashboard_password = os.getenv("DASHBOARD_PASSWORD")

    if not dashboard_password:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    if request.password != dashboard_password:
        raise HTTPException(status_code=401, detail="Invalid password")

    # Create secure token and set cookie
    secure_token = create_secure_token(dashboard_password)

    # Determine if running in production (Vercel)
    is_production = os.getenv("VERCEL_ENV") == "production"

    # Return JSON response with redirect URL
    redirect_url = request.redirect if request.redirect else "/"
    response = JSONResponse({"redirect": redirect_url})

    # Set secure cookie (12 months = 31536000 seconds)
    response.set_cookie(
        key="auth_token",
        value=secure_token,
        max_age=31536000,  # 12 months
        httponly=True,
        secure=is_production,  # True in production with HTTPS
        samesite="lax"
    )

    return response

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Server-rendered dashboard with current escalation data."""
    # Heutigen Report laden
    report = get_today_report()

    # Skala parsen
    scale_lines = ESKALATIONSSKALA.strip().split('\n')
    scale_levels = []
    current_level = None

    for line in scale_lines:
        # Hauptdefinition erkennen: "NUMMER = LABEL: Beschreibung"
        if '=' in line and ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            # Vorherige Stufe abschließen, falls vorhanden
            if current_level:
                scale_levels.append(current_level)

            # Neue Stufe beginnen
            parts = line.split('=', 1)
            if len(parts) == 2:
                num = parts[0].strip()
                rest = parts[1].split(':', 1)
                if len(rest) == 2:
                    label = rest[0].strip()
                    desc = rest[1].strip()
                    try:
                        current_level = {
                            "number": int(num),
                            "label": label,
                            "description": desc
                        }
                    except ValueError:
                        current_level = None
        elif current_level and line.strip() and (line.startswith('   •') or line.startswith('   ') or line.startswith('\t')):
            # Detail-Zeile zur aktuellen Stufe hinzufügen
            current_level["description"] += "\n" + line

    # Letzte Stufe hinzufügen
    if current_level:
        scale_levels.append(current_level)

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