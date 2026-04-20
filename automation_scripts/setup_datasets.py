# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests",
#     "mockseries",
#       "numpy"
# ]
# ///

import os
import hashlib
import requests
import zipfile
import sys
import random
import numpy as np
from datetime import datetime, timedelta
from mockseries.trend import LinearTrend
from mockseries.seasonality import SinusoidalSeasonality
from mockseries.noise import RedNoise
from mockseries.utils import datetime_range

# datasets metadata-
DATASETS = {"ucr_archive": {
    "url": "https://www.cs.ucr.edu/%7Eeamonn/time_series_data_2018/UCRArchive_2018.zip", #confirmed link
    "target_path": "data/UCRArchive_2018.zip",
    "extract_to": "data/UCRArchive_2018/",
    "expected_sha256": "a7163f6edd2b6876d195ab0ee5bcce5ec09873cba75512d35bc64a8a493d9d4a" #hash of the file, to check data consistency
}}

# support functions
def calculate_sha256(filepath):
    """Calculates the SHA-256 fingerprint of a file by reading it in blocks."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, target_path):
    """Downloads a file showing a text progress bar."""
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                sys.stdout.write(f"\rProgress: {percent:.2f}%")
                sys.stdout.flush()
    print("\nDownload completed.")

# deterministic synthetic data generator
def generate_synthetic_dataset(output_path):
    """Generates a synthetic time series of 1 year (1 minute granularity) and saves it in txt."""
    print(f"[*] Synthetic dataset generation in progress (may take a few seconds)...")

    # fixing the seed to ensure reproducibility
    random.seed(42)
    np.random.seed(42) #mock series generator uses numpy so this setting is needed to ensure reproducibility

    # Construction of the signal components
    trend = LinearTrend(coefficient=2, time_unit=timedelta(days=4), flat_base=100)
    seasonality = SinusoidalSeasonality(amplitude=20, period=timedelta(days=7)) \
                  + SinusoidalSeasonality(amplitude=4, period=timedelta(days=1))
    noise = RedNoise(mean=0, std=3, correlation=0.5)

    timeseries = trend + seasonality + noise

    # Timeframe definition: 1 year with 1 measurement per minute
    ts_index = datetime_range(
        granularity=timedelta(minutes=1),
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2023, 12, 31)
    )

    ts_values = timeseries.generate(ts_index)

    # Saving data in pure text format for C++
    with open(output_path, "w") as f:
        for val in ts_values:
            f.write(f"{val}\t") # uses tab instead of line break
        f.write("\n")

    print(f"    [OK] Synthetic dataset saved in {output_path} ({len(ts_values)} timesteps).")

def setup():
    """Coordinates the checking, downloading and generation of datasets."""
    if not os.path.exists("data"):
        os.makedirs("data")

    # Managing real data (UCR Archive)
    for name, info in DATASETS.items():
        path = info["target_path"]

        # checking file zip
        if os.path.exists(path):
            print(f"[*] Dataset '{name}' already present in {path}.")

            # Integrity check (Hash)
            actual_hash = calculate_sha256(path)
            if actual_hash == info["expected_sha256"]:
                print(f"    [OK] The hash matches")
            else:
                print(f"    [WARNING] Hash mismatch! Found: {actual_hash[:8]}...")
        else:
            # Downloading if missing
            print(f"[!] Dataset '{name}' missing.")
            try:
                download_file(info["url"], path)

                # check after download
                if calculate_sha256(path) != info["expected_sha256"]:
                    print(f"    [ERROR] Downloaded file has been corrupted")
            except Exception as e:
                print(f"    [ERROR] Downloading {name} is impossible: {e}")

        # Idempotent extraction
        if info["extract_to"] and not os.path.exists(info["extract_to"]):
            print(f"    Extracting {path}...")
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(info["extract_to"], pwd=b"someone")

    # Synthetic Data Management (Idempotent)
    synthetic_path = "data/synthetic_timeseries.txt"
    if os.path.exists(synthetic_path):
        print(f"[*] Synthetic dataset already present in {synthetic_path}.")
    else:
        generate_synthetic_dataset(synthetic_path)

    print("\n[+] Setup complete. All datasets are ready for the C++ Engine.")

if __name__ == "__main__":
    setup()