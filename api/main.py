import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from risk_engine import hybrid_risk_score

app = FastAPI(
    title="Supply Chain Disruption Risk API",
    description="Hybrid ML + Knowledge Graph risk scoring engine",
    version="1.0"
)

# Serve the HTML dashboard at root
@app.get("/", response_class=HTMLResponse)
def root():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

class RiskRequest(BaseModel):
    country_code: str
    lpi_score: float
    prev_value: float
    event_count: int
    avg_tone: float
    avg_goldstein: float

@app.post("/risk-score")
def get_risk_score(req: RiskRequest):
    result = hybrid_risk_score(
        country_code=req.country_code,
        lpi_score=req.lpi_score,
        prev_value=req.prev_value,
        event_count=req.event_count,
        avg_tone=req.avg_tone,
        avg_goldstein=req.avg_goldstein
    )
    return result

@app.get("/risk-score/{country_code}")
def get_country_risk(country_code: str):
    import pandas as pd
    features = pd.read_csv("ml/features.csv")
    avg = features.mean()
    result = hybrid_risk_score(
        country_code=country_code,
        lpi_score=float(avg["lpi_score"]),
        prev_value=float(avg["prev_value"]),
        event_count=float(avg["event_count"]),
        avg_tone=float(avg["avg_tone"]),
        avg_goldstein=float(avg["avg_goldstein"])
    )
    return result