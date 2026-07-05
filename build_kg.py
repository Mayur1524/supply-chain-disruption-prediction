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
print("Loading countries...")
lpi = pd.read_csv("data/lpi_clean.csv")

with driver.session(database="supplychain") as s:
    s.run("MATCH (n) DETACH DELETE n")  # clear existing
    for _, row in lpi.iterrows():
        s.run("""
            MERGE (c:Country {code: $code})
            SET c.name = $name, c.lpi_score = $lpi
        """, code=row["code"], name=row["country"], lpi=float(row["lpi_score"]))

print(f"  Loaded {len(lpi)} country nodes")

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
        s.run("""
            MERGE (p:Product {code: $code})
            SET p.name = $name
        """, code=int(row["product_code"]),
             name=product_names.get(int(row["product_code"]), str(row["product_code"])))

        s.run("""
            MERGE (c:Country {code: $code})
        """, code=str(row["reporter_code"]))

        s.run("""
            MATCH (c:Country {code: $country_code})
            MATCH (p:Product {code: $prod_code})
            MERGE (c)-[r:EXPORTS {year: $year}]->(p)
            SET r.value_usd = $value
        """, country_code=str(row["reporter_code"]),
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
].head(5000)

with driver.session(database="supplychain") as s:
    for _, row in gdelt_filtered.iterrows():
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
        """, code=str(row["actor1_country"]),
             eid=int(row["event_id"]),
             date=int(row["date"]),
             ecode=str(row["event_code"]),
             gold=float(row["goldstein"]),
             tone=float(row["avg_tone"]),
             articles=int(row["num_articles"]))

print(f"  Loaded {len(gdelt_filtered)} event nodes")

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
        MERGE (semi:Product {code: "8541"})
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
        MATCH (semi:Product {code: "8541"})
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