# Only these 10 countries are in scope. GDELT sometimes reports raw UN
# numeric codes (e.g. "276" for Germany) or non-country actor-type codes
# (e.g. "GOV", "ISRMIL") in the same field — this mapping converts the
# former to the correct ISO3 code already used elsewhere in the graph,
# and lets us skip the latter entirely.
UN_TO_ISO = {
    "156": "CHN", "840": "USA", "276": "DEU", "356": "IND",
    "392": "JPN", "410": "KOR", "826": "GBR", "250": "FRA",
    "764": "THA", "458": "MYS",
}

# GDELT's actor1_country already uses ISO3 codes directly (unlike Comtrade's
# numeric reporter_code) — so here we just need a whitelist of our 10
# in-scope countries, no conversion needed.
VALID_ISO3 = set(UN_TO_ISO.values())
import os
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# ── 1. Load Countries from LPI ────────────────────────
# ── 1. Load Countries from LPI ────────────────────────
print("Loading countries...")
lpi = pd.read_csv("data/lpi_clean.csv")

with driver.session(database="supplychain") as s:
    s.run("MATCH (n) DETACH DELETE n")  # clear existing
    loaded_count = 0
    for _, row in lpi.iterrows():
        if row["code"] not in UN_TO_ISO.values():   # only our 10
            continue
        s.run("""
            MERGE (c:Country {code: $code})
            SET c.name = $name, c.lpi_score = $lpi
        """, code=row["code"], name=row["country"], lpi=float(row["lpi_score"]))
        loaded_count += 1

print(f"  Loaded {loaded_count} country nodes")

# ── 2. Load Trade Routes from Comtrade ────────────────
print("Loading trade routes...")
ct = pd.read_csv("data/comtrade_clean.csv")

product_names = {
    8541: "Semiconductors",
    8471: "Computers",
    3004: "Pharmaceuticals",
    8703: "Vehicles"
}

with driver.session(database="supplychain") as s:
    for _, row in ct.iterrows():
        iso_code = UN_TO_ISO.get(str(row["reporter_code"]))
        if iso_code is None:
            continue   # skip anything outside our 10 countries

        s.run("""
            MERGE (p:Product {code: $code})
            SET p.name = $name
        """, code=int(row["product_code"]),
             name=product_names.get(int(row["product_code"]), str(row["product_code"])))

        s.run("""
            MERGE (c:Country {code: $code})
        """, code=iso_code)

        s.run("""
            MATCH (c:Country {code: $country_code})
            MATCH (p:Product {code: $prod_code})
            MERGE (c)-[r:EXPORTS {year: $year}]->(p)
            SET r.value_usd = $value
        """, country_code=iso_code,
             prod_code=int(row["product_code"]),
             year=int(row["year"]),
             value=float(row["value_usd"]))

print(f"  Loaded {len(ct)} trade relationships")

# ── 3. Load Geopolitical Events from GDELT ────────────
print("Loading geopolitical events...")
gdelt = pd.read_csv("data/gdelt_clean.csv")

gdelt_filtered = gdelt[
    (gdelt["avg_tone"] < -5) |
    (gdelt["goldstein"] < -5)
]

loaded_count = 0
skipped_count = 0

with driver.session(database="supplychain") as s:
    for _, row in gdelt_filtered.iterrows():
        if loaded_count >= 5000:
            break

        # Resolve the raw GDELT code to one of our 10 ISO3 country codes.
        # Skip anything that doesn't resolve — this excludes both raw UN
        # numeric duplicates and non-country actor-type codes.
        iso_code = str(row["actor1_country"])
        if iso_code not in VALID_ISO3:
            skipped_count += 1
            continue

        s.run("""
            MERGE (c:Country {code: $code})
            CREATE (e:Event {
                event_id: $eid,
                date: $date,
                event_code: $ecode,
                goldstein: $gold,
                avg_tone: $tone,
                num_articles: $articles
            })
            CREATE (c)-[:AFFECTED_BY]->(e)
        """, code=iso_code,
             eid=int(row["event_id"]),
             date=int(row["date"]),
             ecode=str(row["event_code"]),
             gold=float(row["goldstein"]),
             tone=float(row["avg_tone"]),
             articles=int(row["num_articles"]))

        loaded_count += 1

print(f"  Loaded {loaded_count} event nodes (skipped {skipped_count} non-scope codes)")

# ── 4. Confluence Provenance: multiple inputs converging at one destination ──
print("Loading confluence provenance example...")

with driver.session(database="supplychain") as s:
    s.run("""
        MERGE (fp:FinishedProduct {name: "Electronic Device"})
        SET fp.category = "Consumer Electronics"
    """)

    s.run("""
        MERGE (taiwan:Country {code: "TWN"})
        SET taiwan.name = "Taiwan"
        MERGE (plastic:Product {code: "3901"})
        SET plastic.name = "Plastic"
        MERGE (taiwan)-[:PRODUCES]->(plastic)
        MERGE (germany:Country {code: "DEU"})
        MERGE (plastic)-[r1:SHIPS_TO {input_type: "raw_material"}]->(germany)
    """)

    s.run("""
        MERGE (china:Country {code: "CHN"})
        MERGE (semi:Product {code: 8541})
        SET semi.name = "Semiconductors"
        MERGE (china)-[:PRODUCES]->(semi)
        MERGE (germany:Country {code: "DEU"})
        MERGE (semi)-[r2:SHIPS_TO {input_type: "component"}]->(germany)
    """)

    s.run("""
        MATCH (germany:Country {code: "DEU"})
        MATCH (fp:FinishedProduct {name: "Electronic Device"})
        MERGE (germany)-[:ASSEMBLES]->(fp)
    """)

    s.run("""
        MATCH (plastic:Product {code: "3901"})
        MATCH (fp:FinishedProduct {name: "Electronic Device"})
        MERGE (plastic)-[:CONTRIBUTES_TO]->(fp)
    """)
    s.run("""
        MATCH (semi:Product {code: 8541})
        MATCH (fp:FinishedProduct {name: "Electronic Device"})
        MERGE (semi)-[:CONTRIBUTES_TO]->(fp)
    """)

print("  Confluence provenance loaded: Taiwan + China -> Germany -> Electronic Device")

# ── 5. Verify ─────────────────────────────────────────
print("\nVerifying graph...")
with driver.session(database="supplychain") as s:
    counts = s.run("""
        MATCH (n)
        RETURN labels(n)[0] AS type, count(n) AS count
        ORDER BY count DESC
    """)
    for record in counts:
        print(f"  {record['type']}: {record['count']} nodes")

driver.close()
print("\nKnowledge Graph built successfully!")