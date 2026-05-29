import os
import requests
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
gloo_client_id = os.getenv("GLOO_CLIENT_ID")
gloo_client_secret = os.getenv("GLOO_CLIENT_SECRET")
gloo_base_url = os.getenv("GLOO_BASE_URL", "https://platform.ai.gloo.com").rstrip('/')
gloo_token_url = os.getenv("GLOO_TOKEN_URL", f"{gloo_base_url}/oauth2/token")
gloo_publisher_id = os.getenv("GLOO_PUBLISHER_ID")

def get_gloo_token():
    if not gloo_client_id or not gloo_client_secret:
        raise ValueError("GLOO_CLIENT_ID and GLOO_CLIENT_SECRET must be set.")
    payload = {
        "grant_type": "client_credentials",
        "client_id": gloo_client_id,
        "client_secret": gloo_client_secret
    }
    response = requests.post(gloo_token_url, data=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def get_headers():
    return {
        "Authorization": f"Bearer {get_gloo_token()}"
    }

def upload_bible_csv(file_path):
    if not gloo_publisher_id:
        print("Error: GLOO_PUBLISHER_ID is not set in .env")
        return
    
    url = f"{gloo_base_url}/ingestion/v2/files"
    
    # Associate the file upload with the Publisher ID for RAG
    data = {
        "publisher_id": gloo_publisher_id
    }
    
    try:
        with open(file_path, "rb") as f:
            files = {"files": (os.path.basename(file_path), f, "text/csv")}
            print(f"Uploading {file_path} to Gloo Publisher {gloo_publisher_id}...")
            response = requests.post(url, headers=get_headers(), data=data, files=files)
            response.raise_for_status()
            print(f"Success! Response: {response.json()}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error uploading {file_path}: {e.response.text}")
    except Exception as e:
        print(f"Failed to upload {file_path}: {e}")

def check_ingestion_status():
    if not gloo_publisher_id:
        print("Error: GLOO_PUBLISHER_ID is not set in .env")
        return
        
    url = f"{gloo_base_url}/engine/v2/publisher/{gloo_publisher_id}/items"
    print(f"\nChecking ingested items for Publisher {gloo_publisher_id}...")
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        items = response.json()
        print(f"Success! Ingested Items:\n{items}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching status: {e.response.text}")
    except Exception as e:
        print(f"Failed to fetch ingestion status: {e}")

# === MAIN ===
if __name__ == "__main__":
    # Use relative paths assuming the CSV files are in the same folder as the script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    english_csv = os.path.join(current_dir, "english_bible.csv")
    tamil_csv = os.path.join(current_dir, "tamil_bible.csv")

    # Upload English Bible
    if os.path.exists(english_csv):
        upload_bible_csv(english_csv)
    else:
        print(f"File not found: {english_csv}")

    # Upload Tamil Bible
    if os.path.exists(tamil_csv):
        upload_bible_csv(tamil_csv)
    else:
        print(f"File not found: {tamil_csv}")
        
    # Check what was ingested
    check_ingestion_status()
