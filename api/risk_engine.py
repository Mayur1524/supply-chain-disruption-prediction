import os
import joblib
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Real-world context for each country (2021-2023 period)
COUNTRY_CONTEXT = {
    "GBR": {
        "events": [
            "Brexit trade disruptions and new customs checks (2021 implementation)",
            "Political instability — 3 Prime Ministers in 2022 (Johnson, Truss, Sunak)",
            "UK-EU trade friction and Northern Ireland Protocol disputes",
            "Energy crisis following Russia-Ukraine war (2022)",
            "Cost of living crisis — highest inflation in 40 years",
            "NHS and public sector strikes affecting logistics workforce",
            "Port congestion at Dover due to post-Brexit border checks"
        ],
        "positives": [
            "Strong financial services sector supports trade financing",
            "High LPI score indicates robust logistics infrastructure"
        ]
    },
    "CHN": {
        "events": [
            "US-China trade war — escalating tariffs on semiconductors and tech",
            "COVID-19 zero-COVID policy causing factory shutdowns (2021-2022)",
            "Shanghai lockdown (April-June 2022) halting port operations",
            "Taiwan strait military tensions increasing shipping risk",
            "Tech export restrictions by US targeting Chinese semiconductor firms",
            "Evergrande debt crisis creating economic uncertainty (2021)",
            "Diplomatic conflicts with Australia, Lithuania, and other trade partners"
        ],
        "positives": [
            "World's largest manufacturing base provides supply chain depth",
            "Rapid post-COVID economic recovery in 2023"
        ]
    },
    "DEU": {
        "events": [
            "Energy dependency on Russian gas disrupted by Ukraine war (2022)",
            "Nord Stream pipeline sabotage causing energy supply crisis",
            "Automotive sector semiconductor shortage (2021-2022)",
            "Rhine river low water levels disrupting inland shipping (2022)",
            "High energy costs forcing factory output reductions"
        ],
        "positives": [
            "Highest LPI score in Europe — world-class logistics infrastructure",
            "Strong industrial base with diversified export markets",
            "Confluence assembly point for Taiwan semiconductors and plastics"
        ]
    },
    "USA": {
        "events": [
            "Port of Los Angeles congestion crisis (2021) — 100+ ships waiting",
            "Trucker shortage causing inland freight delays",
            "Semiconductor shortages hitting automotive and electronics sectors",
            "Inflation Reduction Act disrupting global supply chain agreements",
            "US-China tech decoupling affecting supply chain restructuring"
        ],
        "positives": [
            "Nearshoring trend bringing manufacturing back to North America",
            "Strong domestic consumer demand supporting trade volumes"
        ]
    },
    "IND": {
        "events": [
            "COVID-19 second wave (April-May 2021) severely disrupting manufacturing",
            "Coal shortage causing power cuts to factories (2021)",
            "Pharmaceutical export restrictions on key medicines during COVID",
            "Russia-Ukraine war impacting sunflower oil and fertiliser imports"
        ],
        "positives": [
            "Emerging as key alternative manufacturing hub to China",
            "Growing electronics and pharmaceutical export capacity",
            "Government PLI schemes attracting supply chain investment"
        ]
    },
    "JPN": {
        "events": [
            "Fukushima-related supply chain caution affecting electronics exports",
            "Yen depreciation to 30-year lows increasing import costs (2022)",
            "Semiconductor plant disruptions from extreme weather events",
            "COVID border closures limiting skilled worker mobility (2021-2022)"
        ],
        "positives": [
            "World-class automotive and electronics supply chain management",
            "High LPI score reflects efficient port and customs operations"
        ]
    },
    "KOR": {
        "events": [
            "North Korea missile tests creating regional geopolitical instability",
            "Semiconductor memory chip price volatility (Samsung, SK Hynix)",
            "Urea shortage crisis halting trucking operations (2021)",
            "High energy import dependency amplifying Russia-Ukraine war impact"
        ],
        "positives": [
            "Leading semiconductor and display technology exporter",
            "Strong trade diversification across Asia, US, and Europe"
        ]
    },
    "FRA": {
        "events": [
            "Yellow Vest movement legacy — recurring transport strikes",
            "Energy price crisis following Russia-Ukraine war",
            "Port strikes at Le Havre disrupting container flows (2022)",
            "Pension reform protests causing transport disruptions (2023)"
        ],
        "positives": [
            "Central EU logistics hub with strong rail freight network",
            "Diversified export base across aerospace, agriculture, luxury goods"
        ]
    },
    "THA": {
        "events": [
            "Flooding in industrial estates disrupting electronics manufacturing",
            "Political uncertainty following military government policies",
            "COVID-19 tourism collapse reducing foreign exchange earnings",
            "Chip shortage hitting hard disk drive and electronics exports"
        ],
        "positives": [
            "Key ASEAN manufacturing hub for automotive and electronics",
            "Strong recovery in 2023 with increased foreign investment"
        ]
    },
    "MYS": {
        "events": [
            "COVID-19 factory shutdowns in Penang semiconductor cluster (2021)",
            "Political instability — 3 Prime Ministers in 2 years",
            "Glove manufacturer capacity reduction post-COVID demand crash",
            "Semiconductor fab capacity constraints affecting global chip supply"
        ],
        "positives": [
            "Major global semiconductor packaging and testing hub",
            "Strategic location for ASEAN trade routes"
        ]
    }
}

load_dotenv()

# Load trained models
rf = joblib.load("ml/model_rf.pkl")
xgb = joblib.load("ml/model_xgb.pkl")
cat = joblib.load("ml/model_cat.pkl")

# Connect to Neo4j
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

def get_kg_risk(country_code):
    with driver.session(database="supplychain") as s:
        result = s.run("""
            MATCH (c:Country {code: $code})-[:AFFECTED_BY]->(e:Event)
            WHERE e.goldstein < -5
            RETURN count(e) AS risk_events,
                   avg(e.goldstein) AS avg_severity,
                   avg(e.avg_tone) AS avg_tone
        """, code=country_code)
        record = result.single()
        if record and record["risk_events"] > 0:
            return {
                "risk_events": record["risk_events"],
                "avg_severity": round(record["avg_severity"], 2),
                "avg_tone": round(record["avg_tone"], 2)
            }
        return {"risk_events": 0, "avg_severity": 0, "avg_tone": 0}

def get_confluence_risk(country_code):
    with driver.session(database="supplychain") as s:
        result = s.run("""
            MATCH (origin:Country)-[:PRODUCES]->(input:Product)
                  -[:CONTRIBUTES_TO]->(fp:FinishedProduct)
                  <-[:ASSEMBLES]-(dest:Country {code: $code})
            OPTIONAL MATCH (origin)-[:AFFECTED_BY]->(e:Event)
            WHERE e.goldstein < -5
            RETURN origin.name AS source,
                   input.name AS product,
                   fp.name AS finished_product,
                   count(e) AS source_risk
        """, code=country_code)
        records = result.data()
        return records if records else []

def get_live_news(country_code):
    """Fetch live news from GDELT DOC 2.0 API"""
    COUNTRY_QUERIES = {
        "CHN": "China supply chain",
        "USA": "United States supply chain",
        "DEU": "Germany supply chain",
        "IND": "India supply chain",
        "JPN": "Japan supply chain",
        "KOR": "South Korea supply chain",
        "GBR": "United Kingdom supply chain",
        "FRA": "France supply chain",
        "THA": "Thailand supply chain",
        "MYS": "Malaysia supply chain"
    }
    query = COUNTRY_QUERIES.get(country_code, "supply chain")
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query+ " sourcelang:english",
        "mode": "artlist",
        "maxrecords": 5,
        "format": "json",
        "timespan": "7d"
    }
    # Try twice with short timeouts
    for timeout in [8, 15]:
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                if articles:
                    return [{
                        "title": a.get("title", ""),
                        "url": a.get("url", ""),
                        "source": a.get("domain", ""),
                        "date": a.get("seendate", "")[:8] if a.get("seendate") else "",
                    } for a in articles if a.get("title")]
        except Exception as e:
            print(f"News attempt failed (timeout={timeout}): {e}")
            continue
    return []

def generate_reasoning(country_code, risk_score, risk_level,
                        ml_prob, kg_data, confluence_inputs,
                        lpi_score, event_count, avg_tone, avg_goldstein):

    context = COUNTRY_CONTEXT.get(country_code, {})
    country_events = context.get("events", [])
    country_positives = context.get("positives", [])

    reasons = []
    positives = []

    if country_events:
        reasons.extend(country_events)

    if ml_prob > 0.7:
        reasons.append(f"ML model confirms high disruption probability ({ml_prob*100:.1f}%) based on historical trade pattern analysis")
    elif ml_prob > 0.4:
        reasons.append(f"ML model detects moderate disruption signals ({ml_prob*100:.1f}% probability)")

    if kg_data["risk_events"] > 30:
        reasons.append(f"Knowledge Graph topology: {kg_data['risk_events']} high-severity events (Goldstein < -5) recorded in GDELT 2021-2023")
    elif kg_data["risk_events"] > 10:
        reasons.append(f"Knowledge Graph records {kg_data['risk_events']} significant geopolitical events affecting this country")

    if kg_data["avg_severity"] < -8:
        reasons.append(f"Average event severity is critically high ({kg_data['avg_severity']:.2f}/−10) — extreme conflict-level incidents detected")

    if confluence_inputs:
        high_risk = [c for c in confluence_inputs if c["source_risk"] > 20]
        med_risk = [c for c in confluence_inputs if 5 < c["source_risk"] <= 20]
        for inp in high_risk:
            reasons.append(
                f"CONFLUENCE RISK: {inp['source']} supplies {inp['product']} "
                f"for {inp['finished_product']} assembly — {inp['source_risk']} "
                f"upstream risk events detected"
            )
        for inp in med_risk:
            reasons.append(
                f"CONFLUENCE WARNING: {inp['source']} ({inp['product']}) "
                f"shows {inp['source_risk']} risk events"
            )

    positives.extend(country_positives)

    if lpi_score >= 3.5:
        positives.append(f"Strong logistics performance ({lpi_score:.1f}/5.0) provides supply chain resilience")
    if avg_tone > -2:
        positives.append(f"News sentiment is relatively neutral (tone: {avg_tone:.1f})")
    if kg_data["risk_events"] == 0:
        positives.append("Knowledge Graph shows no high-severity geopolitical events")

    if risk_level == "HIGH":
        summary = "HIGH RISK — Multiple real-world disruption factors identified, confirmed by Knowledge Graph topology analysis and ML pattern recognition."
    elif risk_level == "MEDIUM":
        summary = "MEDIUM RISK — Moderate disruption signals present. Monitor key risk drivers closely."
    else:
        summary = "LOW RISK — Supply chain appears relatively stable. Limited disruption events detected."

    return {
        "summary": summary,
        "risk_drivers": reasons,
        "stabilising_factors": positives,
        "dominant_factor": "KG_TOPOLOGY" if kg_data["risk_events"] > 20 else "ML_PREDICTION" if ml_prob > 0.6 else "BALANCED"
    }

def hybrid_risk_score(country_code, lpi_score, prev_value,
                      event_count, avg_tone, avg_goldstein):

    # ML prediction
    features = np.array([[prev_value, lpi_score,
                          event_count, avg_tone, avg_goldstein]])
    ml_prob = float(cat.predict_proba(features)[0][1])

    # KG reasoning
    kg_data = get_kg_risk(country_code)
    kg_risk_raw = min(kg_data["risk_events"] / 50.0, 1.0)

    # Hybrid combination
    hybrid = (0.6 * ml_prob) + (0.4 * kg_risk_raw)
    final_score = round(hybrid * 100, 1)

    # Risk level
    if final_score >= 70:
        level = "HIGH"
    elif final_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Confluence
    confluence = get_confluence_risk(country_code)

    # Reasoning
    reasoning = generate_reasoning(
        country_code, final_score, level,
        ml_prob, kg_data, confluence,
        lpi_score, event_count, avg_tone, avg_goldstein
    )

   # Live news — fetch with short timeout, return empty if slow
    try:
        live_news = get_live_news(country_code)
    except:
        live_news = []

    return {
        "country_code": country_code,
        "risk_score": final_score,
        "risk_level": level,
        "ml_probability": round(ml_prob, 3),
        "kg_risk_events": kg_data["risk_events"],
        "kg_avg_severity": kg_data["avg_severity"],
        "confluence_inputs": confluence,
        "reasoning": reasoning,
        "live_news": live_news
    }