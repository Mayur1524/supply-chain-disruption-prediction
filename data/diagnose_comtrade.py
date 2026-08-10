import requests
import time

# Only the 3 missing reporters, with full diagnostic output
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

# Just test ONE year first to keep this fast and readable
test_year = "2022"

url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

for r_code, r_name in reporters.items():
    for p_code, p_name in products.items():
        params = {
            "reporterCode": r_code,
            "period": test_year,
            "cmdCode": p_code,
            "flowCode": "X",
            "partnerCode": "0",
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            print(f"\n{r_name} ({r_code}) / {p_name} ({p_code}) / {test_year}")
            print(f"  HTTP status: {r.status_code}")
            body = r.text[:500]
            print(f"  Response snippet: {body}")
        except Exception as e:
            print(f"\n{r_name} / {p_name}: EXCEPTION — {e}")
        time.sleep(1)

print("\nDone.")