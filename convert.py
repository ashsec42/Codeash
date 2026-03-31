import json
import os
import sys
import requests

OUTPUT_FILE_NAME = "playlist.m3u"
EPG_URL = "https://avkb.short.gy/jioepg.xml.gz"

def fetch_data(json_url):
    print("Fetching data from URL...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(json_url, timeout=15, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid JSON received")
        sys.exit(1)


def json_to_m3u(data):
    if not isinstance(data, list):
        print("JSON root must be a list")
        sys.exit(1)

    print(f"Converting {len(data)} streams...")

    m3u_lines = [
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]

    for stream in data:
        if not isinstance(stream, dict):
            continue

        name = stream.get("name", "Unknown")
        logo = stream.get("logo", "")
        url = stream.get("link")

        if not url:
            print(f"Skipping: {name} (no URL)")
            continue

        # --- EXTINF ---
        extinf = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}",{name}'
        m3u_lines.append(extinf)

        # --- DRM ---
        drm_license = stream.get("drmLicense")
        drm_scheme = stream.get("drmScheme")

        if drm_scheme == "clearkey" and drm_license:
            m3u_lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={drm_license}')

        # --- Headers ---
        m3u_lines.append('#EXTVLCOPT:http-user-agent=plaYtv/7.1.3 (Android)')
        
        cookie = stream.get("cookie")
        if cookie:
            m3u_lines.append(f'#EXTHTTP:{{"cookie":"{cookie}"}}')

        # --- URL ---
        m3u_lines.append(url)

    with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"✅ Saved as {OUTPUT_FILE_NAME}")


def main():
    url = os.getenv("JSON_SOURCE_URL")
    if not url:
        print("Set JSON_SOURCE_URL first")
        sys.exit(1)

    data = fetch_data(url)
    json_to_m3u(data)


if __name__ == "__main__":
    main()
