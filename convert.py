# convert.py (WITH STREAM VALIDATION)

import json
import os
import sys
import requests

OUTPUT_FILE_NAME = "playlist.m3u"
EPG_URL = "https://avkb.short.gy/jioepg.xml.gz"

# --- Function to check if a stream URL is live ---
def is_stream_working(url):
    """Checks if the stream URL is reachable by trying a small connection."""
    if not url:
        return False
    try:
        # Use a HEAD request for speed and set a short timeout (e.g., 5 seconds)
        # We check for a successful status code (200-299 range)
        response = requests.head(url, timeout=5, allow_redirects=True)
        return 200 <= response.status_code < 300
    except requests.exceptions.RequestException:
        # Catches connection errors, DNS failure, timeouts, etc.
        return False
# ----------------------------------------------------


def json_to_m3u(json_url):
    """
    Fetches JSON, validates stream URLs, and converts working streams into a detailed M3U format.
    """
    print(f"Fetching data from URL...")
    try:
        response = requests.get(json_url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching or decoding JSON: {e}")
        sys.exit(1)
        
    if not isinstance(data, list):
        print("Error: JSON root must be a list of stream objects. Check your JSON format.")
        sys.exit(1)

    m3u_lines = [
        "#EXTM3U",
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]
    
    working_channel_count = 0
    
    for stream in data:
        channel_name = stream.get('channel_name', 'Unknown Channel')
        stream_url = stream.get('channel_url', '')

        # === STREAM VALIDATION STEP ===
        if not is_stream_working(stream_url):
            print(f"❌ Skipping channel '{channel_name}': URL is not working or timed out.")
            continue
        
        working_channel_count += 1
        
        # --- A. BUILD #EXTINF LINE ---
        extinf_parts = ["#EXTINF:-1"]
        
        # M3U Attributes based on your JSON keys
        if stream.get('channel_id'):
            extinf_parts.append(f'tvg-id="{stream["channel_id"]}"')
        if stream.get('channel_genre'):
            extinf_parts.append(f'group-title="{stream["channel_genre"]}"')
        if stream.get('channel_logo'):
            extinf_parts.append(f'tvg-logo="{stream["channel_logo"]}"')
        
        extinf_line = " ".join(extinf_parts) + f",{channel_name}"
        m3u_lines.append(extinf_line)
        
        # --- B. ADD CUSTOM KODIPROP & HTTP TAGS ---
        
        key_id = stream.get('keyId')
        key = stream.get('key')
        if key_id and key:
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_type=clearkey')
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}')

        m3u_lines.append(f'#EXTVLCOPT:http-user-agent=plaYtv/7.1.3 (Linux;Android 13) ygx/69.1 ExoPlayerLib/824.0')
        
        cookie_value = stream.get('cookie')
        if cookie_value:
            m3u_lines.append(f'#EXTHTTP:{{"cookie":"{cookie_value}"}}')
            
        # 4. Add the stream URL
        m3u_lines.append(stream_url)

    # 5. Write the M3U file
    try:
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines) + '\n')
        print(f"✅ Conversion complete. Wrote {working_channel_count} working streams to {OUTPUT_FILE_NAME}")
    except IOError as e:
        print(f"Error writing to output file {OUTPUT_FILE_NAME}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    url = os.getenv('JSON_SOURCE_URL')
    if not url:
        print("Fatal Error: JSON_SOURCE_URL environment variable is not set.")
        sys.exit(1)
        
    json_to_m3u(url)
