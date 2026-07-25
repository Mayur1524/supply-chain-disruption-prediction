import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from risk_engine import hybrid_risk_score

app = FastAPI(
    title="Supply Chain Disruption Risk API",
    description="Hybrid ML + Knowledge Graph risk scoring engine",
    version="1.0"
)

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
    return hybrid_risk_score(
        country_code=req.country_code,
        lpi_score=req.lpi_score,
        prev_value=req.prev_value,
        event_count=req.event_count,
        avg_tone=req.avg_tone,
        avg_goldstein=req.avg_goldstein
    )

@app.get("/risk-score/{country_code}")
def get_country_risk(country_code: str):
    import pandas as pd
    features = pd.read_csv("ml/features.csv")
    avg = features.mean()
    return hybrid_risk_score(
        country_code=country_code,
        lpi_score=float(avg["lpi_score"]),
        prev_value=float(avg["prev_value"]),
        event_count=float(avg["event_count"]),
        avg_tone=float(avg["avg_tone"]),
        avg_goldstein=float(avg["avg_goldstein"])
    )

@app.get("/trade-routes")
def get_trade_routes():
    import pandas as pd

    UN_TO_ISO = {
        "156": "CHN", "840": "USA", "276": "DEU", "356": "IND",
        "392": "JPN", "410": "KOR", "826": "GBR", "250": "FRA",
        "764": "THA", "458": "MYS",
    }

    PRODUCT_NAMES = {
        8541: "Semiconductors", 8471: "Computers",
        3004: "Pharmaceuticals", 8703: "Vehicles"
    }

    TRADE_DESTINATIONS = {
        ("CHN","Semiconductors"): ["USA","DEU","JPN","KOR"],
        ("CHN","Computers"):      ["USA","GBR","DEU","IND"],
        ("CHN","Pharmaceuticals"):["IND","USA","DEU"],
        ("CHN","Vehicles"):       ["USA","DEU","GBR"],
        ("JPN","Vehicles"):       ["USA","DEU","GBR","FRA"],
        ("JPN","Semiconductors"): ["USA","DEU","KOR"],
        ("JPN","Computers"):      ["USA","DEU"],
        ("JPN","Pharmaceuticals"):["USA","DEU","GBR"],
        ("KOR","Semiconductors"): ["USA","CHN","DEU"],
        ("KOR","Vehicles"):       ["USA","DEU","GBR"],
        ("KOR","Computers"):      ["USA","DEU"],
        ("DEU","Vehicles"):       ["USA","CHN","GBR","FRA"],
        ("DEU","Pharmaceuticals"):["USA","GBR","FRA"],
        ("GBR","Pharmaceuticals"):["USA","DEU","FRA"],
        ("MYS","Semiconductors"): ["USA","CHN","JPN"],
        ("MYS","Computers"):      ["USA","CHN","DEU"],
        ("IND","Pharmaceuticals"):["USA","GBR","DEU"],
        ("THA","Vehicles"):       ["DEU","JPN","USA"],
        ("FRA","Pharmaceuticals"):["USA","DEU","GBR"],
        ("FRA","Vehicles"):       ["DEU","GBR","USA"],
    }

    ct = pd.read_csv("data/comtrade_clean.csv")
    ct["iso_code"] = ct["reporter_code"].astype(str).map(UN_TO_ISO)
    ct = ct.dropna(subset=["iso_code"])

    latest = ct.sort_values("year").groupby(
        ["iso_code","product_code"]
    ).last().reset_index()

    routes = []
    for _, row in latest.iterrows():
        iso = row["iso_code"]
        product = PRODUCT_NAMES.get(int(row["product_code"]), str(row["product_code"]))
        destinations = TRADE_DESTINATIONS.get((iso, product), [])
        value = float(row["value_usd"])
        value_per_dest = value / max(len(destinations), 1)

        for dest in destinations:
            routes.append({
                "from": iso,
                "to": dest,
                "product": product,
                "value_usd": round(value, 0),
                "value_display": f"${round(value/1e9,1)}B total",
                "value_per_dest": f"${round(value_per_dest/1e9,1)}B",
                "year": int(row["year"]),
                "mode": "Sea" if iso in ["CHN","JPN","KOR","MYS","THA","IND"] else "Sea/Land"
            })

    return {"routes": routes, "total": len(routes)}
@app.get("/news/{country_code}")
def get_news(country_code: str):
    from risk_engine import get_live_news
    news = get_live_news(country_code)
    return {"news": news}