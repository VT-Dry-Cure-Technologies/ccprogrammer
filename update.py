import os
import requests
import tarfile
import json
from pathlib import Path

FIRMWARE_DIR = Path(__file__).parent / "firmware"
VERSION_JSON = FIRMWARE_DIR / "version.json"
API_URL = "https://edlquuxypulyedwgweai.supabase.co/functions/v1/getFirmware"

def fetch_firmware_info():
    resp = requests.get(API_URL)
    resp.raise_for_status()
    return resp.json()

def download_firmware(url, dest_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_tar_gz(tar_path, extract_to):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_to)

def write_version_json(info):
    FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
    with open(VERSION_JSON, 'w') as f:
        json.dump(info, f, indent=4)

def get_current_version():
    try:
        with open(VERSION_JSON, 'r') as f:
            return json.load(f)["version"]
    except FileNotFoundError:
        return "NONE"

def update_firmware():
    # Check for internet connection
    try:
        requests.get("https://www.google.com", timeout=5)
    except requests.exceptions.RequestException:
        return "No internet connection"

    print("Fetching firmware info...")
    info = fetch_firmware_info()
    url = info["url"]
    version = info["version"]
    if get_current_version() != "NONE" and version <= get_current_version():
        return "No update available"
    
    print(f"Firmware URL: {url}\nVersion: {version}")

    FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = FIRMWARE_DIR / "firmware.tar.gz"

    print("Downloading firmware archive...")
    download_firmware(url, tar_path)

    print("Extracting firmware...")
    extract_tar_gz(tar_path, FIRMWARE_DIR)

    print("Writing version info...")
    write_version_json({"url": url, "version": version})

    print("Cleaning up...")
    os.remove(tar_path)
    print("Update complete.")
    return "Success"

if __name__ == "__main__":
    update_firmware() 