import os
import sys
import requests

# The filename you want to save locally
OUTPUT_FILE_NAME = "playlist.m3u"

# The OTT Navigator User-Agent that bypasses the 403 error
OTT_UA = "OTT-Navigator/1.7.1.1 (Android/11; Mobile; en_US)"

def download_m3u(url):
    print(f"Connecting to source as OTT Navigator...")

    headers = {
        "User-Agent": OTT_UA,
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

    try:
        # We use stream=True for larger M3U files to handle memory efficiently
        response = requests.get(url, headers=headers, timeout=20, stream=True)
        response.raise_for_status()

        with open(OUTPUT_FILE_NAME, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Successfully downloaded: {OUTPUT_FILE_NAME}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download: {e}")
        sys.exit(1)

def main():
    # Get the link from your environment variable
    url = os.getenv("M3U_SOURCE_URL")

    if not url:
        print("ERROR: Please set M3U_SOURCE_URL (e.g., export M3U_SOURCE_URL='http://...')")
        sys.exit(1)

    download_m3u(url)

if __name__ == "__main__":
    main()
