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
import argparse
import numpy as np
from datetime import datetime, timedelta
from mockseries.trend import LinearTrend
from mockseries.seasonality import SinusoidalSeasonality
from mockseries.noise import RedNoise
from mockseries.utils import datetime_range

# datasets metadata
DATASETS = {"ucr_archive": {
    "url": "https://www.cs.ucr.edu/%7Eeamonn/time_series_data_2018/UCRArchive_2018.zip", #confirmed link
    "target_path": "data/UCRArchive_2018.zip",
    "extract_to": "data",
    "check_dir": "data/UCRArchive_2018/CinCECGTorso",
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
def generate_synthetic_dataset(output_path, num_series, series_length):
    """Generates N synthetic time series of length L and saves them in txt."""
    print(f"[*] Synthetic dataset generation: {num_series} series of {series_length} timesteps...")

    # fixing the seed to ensure reproducibility
    random.seed(42)
    np.random.seed(42)

    # Construction of the signal components
    trend = LinearTrend(coefficient=2, time_unit=timedelta(days=4), flat_base=100)
    seasonality = SinusoidalSeasonality(amplitude=20, period=timedelta(days=7)) \
                  + SinusoidalSeasonality(amplitude=4, period=timedelta(days=1))

    timeseries_base = trend + seasonality

    # Timeframe definition: 1 minute = 1 timestep
    ts_index = datetime_range(
        granularity=timedelta(minutes=1),
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2023, 1, 1) + timedelta(minutes=series_length)
    )

    base_values = timeseries_base.generate(ts_index)

    x_axis = np.linspace(0, 50 * np.pi, series_length)

    # Saving data in pure text format for C++ (TSV format)
    with open(output_path, "w") as f:
        for i in range(num_series):
            # 1. base noise
            noise = np.random.normal(0, 3, series_length)

            # 2. UNIQUE SHAPE: Frequency, Phase and Amplitude randomized for THIS row
            freq = np.random.uniform(0.1, 3.0)       # How "thick" the waves are
            phase = np.random.uniform(0, 2 * np.pi)  # Where does the wave come from?
            amplitude = np.random.uniform(10, 50)    # How high is the wave

            unique_wave = amplitude * np.sin(freq * x_axis + phase)

            # 3. combining: Base + Single Wave + Noise
            series_values = base_values + unique_wave + noise

            f.write("\t".join(f"{val:.4f}" for val in series_values) + "\n")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"    [OK] Synthetic dataset saved in {output_path} ({file_size_mb:.1f} MB).")

def setup(num_series, series_length):
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
        if not os.path.exists(info["check_dir"]):
            print(f"    Extraction of {path} is running (may take some time)...")
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(info["extract_to"], pwd=b"someone")
            print("    [OK] Extraction has been completed.")
        else:
            print("    [*] Archive already extracted successfully.")

    # Synthetic Data Management (Idempotent)
    synthetic_path = "data/synthetic_timeseries.txt"
    if os.path.exists(synthetic_path):
        print(f"[*] Removing old synthetic dataset to apply new parameters...")
        os.remove(synthetic_path)

    generate_synthetic_dataset(synthetic_path, num_series, series_length)

    print("\n[+] Setup completed. All datasets are ready for the C++ Engine.")

if __name__ == "__main__":
    # Initialize the parser to read commands from the terminal
    parser = argparse.ArgumentParser(description="HPC Dataset Generator")

    # Defines the two optional parameters with their default values
    parser.add_argument("--num-series", type=int, default=100, help="Number of synthetic time series")
    parser.add_argument("--length", type=int, default=65536, help="Length of each time series (timesteps)")

    # "Captures" the values written by the user in the terminal
    args = parser.parse_args()

    # Calls the function passing it the two extracted numbers
    setup(args.num_series, args.length)