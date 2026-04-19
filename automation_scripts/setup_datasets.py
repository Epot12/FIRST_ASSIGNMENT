import os
import hashlib
import requests
import zipfile
import sys

# DATASET MANIFEST
# SHA-256 hash reported below are an example. to be calculated on the real files
DATASETS = {
    "ucr_archive": {
        "url": "https://www.cs.ucr.edu/~eamonn/time_series_data_2018/UCRArchive_2018.zip",
        "target_path": "data/UCRArchive_2018.zip",
        "extract_to": "data/UCRArchive_2018/",
        "expected_sha256": "8f32... (il tuo hash) ..."
    },
    "bitcoin_data": {
        "url": "https://raw.githubusercontent.com/tuo_utente/tuo_repo/main/data/bitcoin_close_1m.txt",
        "target_path": "data/bitcoin_close_1m.txt",
        "extract_to": None,
        "expected_sha256": "4e1a... (il tuo hash) ..."
    }
}

def calculate_sha256(filepath):
    """Calcola l'impronta digitale SHA-256 di un file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Legge il file a blocchi per non intasare la RAM se il file è enorme
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, target_path):
    """Scarica un file con barra di progresso testuale."""
    print(f"Scaricando {url}...")
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
                sys.stdout.write(f"\rProgresso: {percent:.2f}%")
                sys.stdout.flush()
    print("\nDownload completato.")

def setup():
    if not os.path.exists("data"):
        os.makedirs("data")

    for name, info in DATASETS.items():
        path = info["target_path"]

        # 1. Verifica presenza
        if os.path.exists(path):
            print(f"[*] Dataset '{name}' già presente in {path}.")

            # 2. Verifica Integrità (La parte professionale)
            actual_hash = calculate_sha256(path)
            if actual_hash == info["expected_sha256"]:
                print(f"    [OK] L'impronta digitale corrisponde.")
            else:
                print(f"    [WARNING] Versione differente! Trovato: {actual_hash[:8]}... ma mi aspettavo: {info['expected_sha256'][:8]}...")
                print(f"    Il benchmark potrebbe dare risultati diversi dai miei.")
        else:
            # 3. Download se mancante
            print(f"[!] Dataset '{name}' mancante.")
            try:
                download_file(info["url"], path)

                # Verifica immediata dopo il download
                if calculate_sha256(path) != info["expected_sha256"]:
                    print(f"    [ERRORE] Il file scaricato è corrotto o diverso dall'originale.")
            except Exception as e:
                print(f"    [ERRORE] Impossibile scaricare {name}: {e}")

        # 4. Estrazione se necessario
        if info["extract_to"] and not os.path.exists(info["extract_to"]):
            print(f"    Estraendo {path}...")
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(info["extract_to"])

if __name__ == "__main__":
    setup()