import pandas as pd
import os
import glob

os.makedirs("data", exist_ok=True)

# ── 1. Clean LPI ──────────────────────────────────────
print("Cleaning LPI data...")
lpi = pd.read_csv("data/lpi_extracted/API_LP.LPI.OVRL.XQ_DS2_en_csv_v2_300824.csv", skiprows=4)

# Use most recent available year first, falling back through known LPI survey years
year_cols = ["2023", "2018", "2016", "2014", "2012", "2010", "2007"]
year_cols = [y for y in year_cols if y in lpi.columns]  # only keep columns that actually exist
lpi["lpi_score"] = lpi[year_cols].bfill(axis=1).iloc[:, 0]
lpi = lpi[["Country Name", "Country Code", "lpi_score"]].copy()
lpi.columns = ["country", "code", "lpi_score"]
lpi["lpi_score"] = pd.to_numeric(lpi["lpi_score"], errors="coerce")
lpi = lpi.dropna()
lpi.to_csv("data/lpi_clean.csv", index=False)
print(f"  LPI clean: {len(lpi)} countries saved")

# ── 2. Clean Comtrade ─────────────────────────────────
print("Cleaning Comtrade data...")
ct = pd.read_csv("data/comtrade_raw.csv")
ct = ct[["refYear", "reporterCode", "reporterISO",
          "flowCode", "cmdCode", "primaryValue"]].copy()
ct.columns = ["year", "reporter_code", "reporter_iso",
               "flow", "product_code", "value_usd"]
ct["value_usd"] = pd.to_numeric(ct["value_usd"], errors="coerce")
ct = ct.dropna(subset=["value_usd"])
ct.to_csv("data/comtrade_clean.csv", index=False)
print(f"  Comtrade clean: {len(ct)} records saved")

# ── 3. Clean GDELT ────────────────────────────────────
print("Cleaning GDELT data...")
gdelt_cols = [0,1,5,6,15,30,31,34]
col_names = ["event_id","date","actor1_country",
             "actor2_country","event_code",
             "goldstein","num_articles","avg_tone"]
files = glob.glob("data/gdelt_raw/*.CSV")
gdelt_frames = []
for f in files:
    try:
        df = pd.read_csv(f, sep="\t", header=None,
                         usecols=gdelt_cols,
                         names=col_names,
                         on_bad_lines="skip")
        gdelt_frames.append(df)
    except Exception as e:
        print(f"  Skipping {f}: {e}")

gdelt = pd.concat(gdelt_frames, ignore_index=True)
gdelt = gdelt.dropna(subset=["actor1_country"])
gdelt.to_csv("data/gdelt_clean.csv", index=False)
print(f"  GDELT clean: {len(gdelt)} events saved")

print("\nAll datasets cleaned and ready!")