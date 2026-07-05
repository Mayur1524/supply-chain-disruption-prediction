import requests
import zipfile
import os

os.makedirs("data", exist_ok=True)

# Download GDELT 2021 - Suez Canal year (most relevant for your project)
urls = [
    "http://data.gdeltproject.org/events/20210101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20210601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20211201.export.CSV.zip",
    "http://data.gdeltproject.org/events/20220101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20220601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20230101.export.CSV.zip",
]

for url in urls:
    filename = url.split("/")[-1]
    print(f"Downloading {filename}...")
    r = requests.get(url, stream=True)
    zip_path = f"data/{filename}"
    with open(zip_path, "wb") as f:
        f.write(r.content)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall("data/gdelt_raw")
    os.remove(zip_path)
    print(f"  Done")

print("\nAll GDELT files downloaded into data/gdelt_raw/")