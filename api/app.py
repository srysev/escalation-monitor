# api/app.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.storage import get_current_score, get_latest_metrics

app = FastAPI(title="Escalation Monitor API")

@app.get("/score")
def score():
    return {"score": get_current_score()}  # 1..10

@app.get("/metrics")
def metrics():
    return JSONResponse(get_latest_metrics())