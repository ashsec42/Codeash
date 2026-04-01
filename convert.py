import os
import sys
import requests

# The name of the file that will be saved in your repository
OUTPUT_FILE_NAME = "playlist.m3u"

# The specific User-Agent required by the source
OTT_UA = "OTT-Navigator/1.7.1.1 (Android/11; Mobile; en_US)"

def download_m3u():
    # This pulls the URL from the GitHub Secret you will set up
    url = os.getenv("M3U_SOURCE_URL")
    
    if not url:
        print("❌ ERROR: M3U_SOURCE_URL environment variable is not set.")
        sys.exit(1)

    print(f"Requesting source using OTT Navigator headers...")

    headers = {
        "User-Agent": OTT_UA,
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

    try:
        # stream=True is safer for large M3U files
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        
        # This triggers an error if the server returns 403, 404, etc.
        response.raise_for_status()

        with open(OUTPUT_FILE_NAME, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Successfully updated {OUTPUT_FILE_NAME}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_m3u()
