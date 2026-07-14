import requests
import zipfile
import os

os.makedirs("data", exist_ok=True)

# Extended to 2018-2023 for more training data
urls = [
    # 2018
    "http://data.gdeltproject.org/events/20180101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20180601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20181201.export.CSV.zip",
    # 2019
    "http://data.gdeltproject.org/events/20190101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20190601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20191201.export.CSV.zip",
    # 2020 (COVID year — most valuable disruption signal)
    "http://data.gdeltproject.org/events/20200101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20200601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20201201.export.CSV.zip",
    # 2021 (already had these)
    "http://data.gdeltproject.org/events/20210101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20210601.export.CSV.zip",
    "http://data.gdeltproject.org/events/20211201.export.CSV.zip",
    # 2022
    "http://data.gdeltproject.org/events/20220101.export.CSV.zip",
    "http://data.gdeltproject.org/events/20220601.export.CSV.zip",
    # 2023
    "http://data.gdeltproject.org/events/20230101.export.CSV.zip",
]

for url in urls:
    filename = url.split("/")[-1]
    print(f"Downloading {filename}...")
    try:
        r = requests.get(url, stream=True, timeout=60)
        zip_path = f"data/{filename}"
        with open(zip_path, "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall("data/gdelt_raw")
        os.remove(zip_path)
        print(f"  Done")
    except Exception as e:
        print(f"  Error: {e}")

print("\nAll GDELT files downloaded into data/gdelt_raw/")