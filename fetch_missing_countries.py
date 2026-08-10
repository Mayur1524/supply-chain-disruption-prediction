import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("UN_COMTRADE_API_KEY")
if not API_KEY:
    print("ERROR: UN_COMTRADE_API_KEY not found in .env")
    print("Add a line like: UN_COMTRADE_API_KEY=your_key_here")
    exit()

reporters = {
    "840": "USA",
    "356": "India",
    "250": "France",
}

products = {
    "8541": "Semiconductors",
    "8471": "Computers",
    "3004": "Pharmaceuticals",
    "8703": "Vehicles",
}

years = ["2018", "2019", "2020", "2021", "2022", "2023"]

url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

all_data = []

for year in years:
    print(f"\n--- Downloading year {year} ---")
    for r_code, r_name in reporters.items():
        for p_code, p_name in products.items():
            params = {
                "reporterCode": r_code,
                "period": year,
                "cmdCode": p_code,
                "flowCode": "X",
                "partnerCode": "0",
            }
            try:
                r = requests.get(url, params=params, headers=headers, timeout=30)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    if data:
                        all_data.extend(data)
                        print(f"  {r_name} {p_name} {year}: {len(data)} records")
                    else:
                        print(f"  {r_name} {p_name} {year}: 0 records (genuinely no data)")
                elif r.status_code == 429:
                    print(f"  {r_name} {p_name} {year}: rate limited, waiting 5s and retrying...")
                    time.sleep(5)
                    r = requests.get(url, params=params, headers=headers, timeout=30)
                    if r.status_code == 200:
                        data = r.json().get("data", [])
                        if data:
                            all_data.extend(data)
                            print(f"    retry succeeded: {len(data)} records")
                else:
                    print(f"  {r_name} {p_name} {year}: HTTP {r.status_code} - {r.text[:150]}")
                time.sleep(2)
            except Exception as e:
                print(f"  Error {r_name} {p_name} {year}: {e}")

df = pd.DataFrame(all_data)
df.to_csv("data/comtrade_missing_countries_raw.csv", index=False)
print(f"\nTotal saved: {len(df)} records to data/comtrade_missing_countries_raw.csv")