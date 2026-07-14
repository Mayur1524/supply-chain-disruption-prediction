import requests
import json

# Test China
print("Testing China...")
r1 = requests.post('http://127.0.0.1:8000/risk-score', json={
    'country_code': 'CHN',
    'lpi_score': 3.61,
    'prev_value': 65000000000,
    'event_count': 8867,
    'avg_tone': -1.2,
    'avg_goldstein': 0.99
})
print(json.dumps(r1.json(), indent=2))

# Test Germany
print("\nTesting Germany...")
r2 = requests.post('http://127.0.0.1:8000/risk-score', json={
    'country_code': 'DEU',
    'lpi_score': 4.2,
    'prev_value': 45000000000,
    'event_count': 100,
    'avg_tone': -0.5,
    'avg_goldstein': 1.2
})
print(json.dumps(r2.json(), indent=2))