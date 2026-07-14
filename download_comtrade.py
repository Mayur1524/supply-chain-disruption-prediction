import requests
import pandas as pd
import os
import time

os.makedirs("data", exist_ok=True)

reporters = {
    "156": "China",
    "840": "USA",
    "276": "Germany",
    "356": "India",
    "392": "Japan",
    "410": "South Korea",
    "826": "UK",
    "250": "France",
    "764": "Thailand",
    "458": "Malaysia"
}

products = {
    "8541": "Semiconductors",
    "8471": "Computers",
    "3004": "Pharmaceuticals",
    "8703": "Vehicles"
}

# Request ONE year at a time to avoid API limits
years = ["2018", "2019", "2020", "2021", "2022", "2023"]

all_data = []

for year in years:
    print(f"\n--- Downloading year {year} ---")
    for r_code, r_name in reporters.items():
        for p_code, p_name in products.items():
            url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
            params = {
                "reporterCode": r_code,
                "period": year,
                "cmdCode": p_code,
                "flowCode": "X",
                "partnerCode": "0"
            }
            try:
                r = requests.get(url, params=params, timeout=30)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    if data:
                        all_data.extend(data)
                        print(f"  {r_name} {p_name} {year}: {len(data)} records")
                time.sleep(1)
            except Exception as e:
                print(f"  Error {r_name} {p_name}: {e}")

df = pd.DataFrame(all_data)
df.to_csv("data/comtrade_raw.csv", index=False)
print(f"\nTotal saved: {len(df)} records to data/comtrade_raw.csv")