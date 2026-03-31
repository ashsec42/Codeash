import json
import os
import sys
import requests

OUTPUT_FILE_NAME = "playlist.m3u"
EPG_URL = "https://avkb.short.gy/jioepg.xml.gz"

def fetch_data(url):
    print("Fetching Zee5 JSON...")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("Invalid JSON received")
        sys.exit(1)


def json_to_m3u(data):
    # ✅ Expect ONLY Zee5 format
    channels = data.get("channels")

    if not isinstance(channels, list):
        print("Error: 'channels' list not found in JSON")
        sys.exit(1)

    print(f"Converting {len(channels)} Zee5 channels...")

    m3u_lines = [
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]

    for ch in channels:
        if not isinstance(ch, dict):
            continue

        name = ch.get("name", "Unknown")
        logo = ch.get("logo", "")
        url = ch.get("mpd")

        if not url:
            print(f"Skipping {name} (no MPD)")
            continue

        # --- EXTINF ---
        m3u_lines.append(
            f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="ZEE5",{name}'
        )

        # --- DRM (ClearKey) ---
        clearkey = ch.get("clearkey")

        if clearkey:
            key_id = clearkey.get("keyId")
            key = clearkey.get("key")

            if key_id and key:
                m3u_lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
                m3u_lines.append(
                    f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}'
                )
            else:
                print(f"Warning: Missing DRM keys for {name}")

        else:
            print(f"Warning: No DRM info for {name}")

        # --- USER AGENT ---
        m3u_lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')

        # --- STREAM URL ---
        m3u_lines.append(url)

    try:
        with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")

        print(f"✅ Zee5 playlist saved as {OUTPUT_FILE_NAME}")

    except IOError as e:
        print(f"Error writing file: {e}")
        sys.exit(1)


def main():
    url = os.getenv("JSON_SOURCE_URL")

    if not url:
        print("ERROR: Please set JSON_SOURCE_URL")
        sys.exit(1)

    data = fetch_data(url)
    json_to_m3u(data)


if __name__ == "__main__":
    main()
