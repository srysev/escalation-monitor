# src/app.py
import os
import sys
from urllib.parse import quote
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.storage import get_today_report
from src.agents.review import ESKALATIONSSKALA
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import stytch
from stytch.core.response_base import StytchError

app = FastAPI(title="Escalation Monitor API")
templates = Jinja2Templates(directory="src/templates")

# --- Stytch Configuration ---
STYTCH_PROJECT_ID = os.getenv("STYTCH_PROJECT_ID")
STYTCH_SECRET = os.getenv("STYTCH_SECRET")
STYTCH_ENVIRONMENT = os.getenv("STYTCH_ENVIRONMENT", "test")

# Initialize Stytch client
stytch_client = None
if STYTCH_PROJECT_ID and STYTCH_SECRET:
    stytch_client = stytch.Client(
        project_id=STYTCH_PROJECT_ID,
        secret=STYTCH_SECRET,
        environment=STYTCH_ENVIRONMENT,
    )
else:
    print("WARNING: Stytch credentials not configured. Authentication will be disabled.", file=sys.stderr)

# --- Helper: Get authenticated user ---
def get_authenticated_user(request: Request):
    """Validate JWT session and return Stytch user or None."""
    if not stytch_client:
        return None

    session_jwt = request.cookies.get("stytch_session_jwt")
    if not session_jwt:
        return None

    try:
        resp = stytch_client.sessions.authenticate_jwt(session_jwt=session_jwt)
        return resp.session.user_id, resp.session
    except StytchError:
        return None

# --- Auth Middleware ---
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # If Stytch is not configured, skip authentication
    if not stytch_client:
        response = await call_next(request)
        return response

    # Define public paths that don't require authentication
    public_paths = ["/login", "/auth/send-magic-link", "/authenticate"]
    public_static_extensions = [".css", ".js", ".png", ".ico", ".svg", ".html"]

    # Check if current path is public
    path = request.url.path
    if (path in public_paths or
        any(path.endswith(ext) for ext in public_static_extensions) or
        path.startswith("/public/")):
        response = await call_next(request)
        return response

    # Check JWT authentication
    user = get_authenticated_user(request)
    if not user:
        # Redirect to login page with return URL
        return RedirectResponse(
            url=f"/login?redirect={quote(request.url.path)}",
            status_code=302
        )

    # Store authenticated user in request.state for reuse in route handlers
    request.state.user_info = user

    # Authentication successful, proceed with request
    response = await call_next(request)
    return response

# deactivated because Vercel says: app.mount("/public", ...) is not needed and should not be used. ---Mount static files for serving login.html
#app.mount("/public", StaticFiles(directory="public"), name="public")

# --- Authentication Routes ---
class MagicLinkRequest(BaseModel):
    email: str
    redirect: str = "/"

@app.get("/login")
async def login_page(request: Request):
    """Redirect to static login page with redirect parameter."""
    redirect_target = request.query_params.get("redirect")
    if redirect_target:
        safe_target = quote(redirect_target, safe="/")
        return RedirectResponse(f"/login.html?redirect={safe_target}", status_code=307)
    return RedirectResponse("/login.html", status_code=307)

@app.post("/auth/send-magic-link")
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link to existing user's email."""
    if not stytch_client:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    try:
        # Use send() instead of login_or_create() to only allow existing users
        resp = stytch_client.magic_links.email.send(
            email=request.email
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send magic link")

        return JSONResponse({"message": "Magic link sent! Check your inbox."})

    except StytchError as e:
        # Stytch returns 404 with error_type="user_not_found" if user doesn't exist
        error_str = str(e).lower()
        if "user_not_found" in error_str or "404" in error_str:
            raise HTTPException(
                status_code=403,
                detail="Diese E-Mail-Adresse ist nicht registriert. Bitte kontaktieren Sie den Administrator."
            )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/authenticate")
async def authenticate(request: Request):
    """Authenticate magic link token and set JWT cookie."""
    if not stytch_client:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    try:
        # Authenticate magic link with 60 days session duration
        resp = stytch_client.magic_links.authenticate(
            token=token,
            session_duration_minutes=87600  # 60 days (2 months)
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Determine if running in production
        is_production = os.getenv("VERCEL_ENV") == "production"

        # Create response and set JWT cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="stytch_session_jwt",
            value=resp.session_jwt,
            max_age=87600 * 60,  # 60 days in seconds
            httponly=True,
            secure=is_production,
            samesite="lax"  # Allow cookie on top-level navigation (e.g., from magic link)
        )

        return response

    except StytchError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/logout")
async def logout():
    """Logout user by clearing session cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="stytch_session_jwt")
    return response

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Server-rendered dashboard with current escalation data."""
    # Get authenticated user info from request.state (set by middleware)
    # This avoids a second authenticate_jwt() API call
    user_info = getattr(request.state, 'user_info', None)
    user_email = None
    # TODO: Implement user email display later if needed
    # For now, just check if user is authenticated (user_info is not None)

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

    # Timestamp formatieren (UTC -> Europa/Berlin)
    if report and "timestamp" in report:
        try:
            dt_utc = datetime.fromisoformat(report["timestamp"].replace('Z', '+00:00'))
            dt_berlin = dt_utc.astimezone(ZoneInfo("Europe/Berlin"))
            formatted_timestamp = dt_berlin.strftime("%d.%m.%Y, %H:%M Uhr")
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
            "formatted_timestamp": formatted_timestamp,
            "user_email": user_email
        }
    )