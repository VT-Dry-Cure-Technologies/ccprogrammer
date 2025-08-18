import os
import requests
import tarfile
import json
from pathlib import Path
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://edlquuxypulyedwgweai.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVkbHF1dXh5cHVseWVkd2d3ZWFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk0Nzg3OTAsImV4cCI6MjA1NTA1NDc5MH0.EL4k_9sOoD9NR6sjVnJj0IjT5SoRYsDrktsdPH1dTgo"

def create_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_firmware_info():
    supabase = create_supabase_client()
    
    # Query the firmwares table to get the latest row
    response = supabase.table('firmwares').select('link, version, created_at').order('created_at', desc=True).limit(1).execute()
    
    if not response.data:
        raise Exception("No firmware records found in database")
    
    latest_firmware = response.data[0]
    print(f"Latest firmware: {latest_firmware}")
    return {
        "url": latest_firmware["link"],
        "version": latest_firmware["version"],
        "created_at": latest_firmware["created_at"]
    }

def download_firmware(url, dest_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_tar_gz(tar_path, extract_to):
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_to)

def write_version_json(info, firmware_dir):
    firmware_dir.mkdir(parents=True, exist_ok=True)
    version_json = firmware_dir / "version.json"
    with open(version_json, 'w') as f:
        json.dump(info, f, indent=4)


def get_current_version_and_created_at(firmware_dir):
    version_json = firmware_dir / "version.json"
    try:
        with open(version_json, 'r') as f:
            data = json.load(f)
            print(f"Current version: {data['version']}, created_at: {data['created_at']}")
            return data["version"], datetime.fromisoformat(data["created_at"])
    except FileNotFoundError:
        return "NONE", "NONE"


def update_firmware(firmware_dir=None):
    if firmware_dir is None:
        firmware_dir = Path.home() / "firmwares" / "main"
    
    # Check for internet connection
    try:
        requests.get("https://www.google.com", timeout=5)
    except requests.exceptions.RequestException:
        return "No internet connection"
    print(f"Firmware directory: {firmware_dir}")
    print("Fetching firmware info...")
    info = fetch_firmware_info()
    url = info["url"]
    version = info["version"]
    created_at = datetime.fromisoformat(info["created_at"])
    current_version, current_created_at = get_current_version_and_created_at(firmware_dir)
    if current_version != "NONE" and version <= current_version and created_at <= current_created_at:
        print(f"No update available")
        return "No update available"
    
    print(f"Firmware URL: {url}\nVersion: {version}")

    firmware_dir.mkdir(parents=True, exist_ok=True)
    tar_path = firmware_dir / "firmware.tar.gz"

    print(f"Downloading firmware archive {url} to {tar_path}")
    download_firmware(url, tar_path)

    print(f"Extracting firmware {tar_path} to {firmware_dir}")
    extract_tar_gz(tar_path, firmware_dir)

    print(f"Writing version info {firmware_dir}")
    write_version_json({"url": url, "version": version, "created_at": info["created_at"]}, firmware_dir)

    print("Cleaning up...")
    os.remove(tar_path)
    print("Update complete.")
    return "Success"

if __name__ == "__main__":
    update_firmware() 
