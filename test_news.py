import requests

url = "https://api.gdeltproject.org/api/v2/doc/doc"
params = {
    "query": "supply chain disruption",
    "mode": "artlist",
    "maxrecords": 10,
    "format": "json"
}
r = requests.get(url, params=params)
print(r.status_code)
print(r.json())