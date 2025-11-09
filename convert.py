import json
import os
import sys
import requests

OUTPUT_FILE_NAME = "playlist.m3u"
# Define the EPG URL for the M3U Header
EPG_URL = "https://avkb.short.gy/jioepg.xml.gz"

def fetch_data(json_url):
    """
    Fetches JSON from a URL with robust error handling.
    """
    print(f"Fetching data from URL...")
    # Add a common User-Agent to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    
    try:
        response = requests.get(json_url, timeout=15, headers=headers)
        # Check for HTTP errors (404, 403, 500, etc.)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP Error: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch URL: {e}")
        sys.exit(1)

    # Now, try to decode the JSON
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Failed to decode JSON. The response is not valid JSON.")
        print("This often happens on a 404 page or if the API returns an HTML error.")
        print("--- Response Text (first 500 chars) ---")
        print(response.text[:500])
        print("---------------------------------")
        sys.exit(1)
        
    return data

def json_to_m3u(data):
    """
    Converts the JSON (as a LIST) into a detailed M3U format.
    """
    
    # 1. NEW: Check if the JSON root is a LIST
    if not isinstance(data, list):
        print(f"Error: JSON root must be a list of stream objects. Got: {type(data)}")
        sys.exit(1)

    print(f"Successfully fetched {len(data)} stream objects (as a list). Converting...")

    m3u_lines = [
        "#EXTM3U",
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]
    
    # 2. NEW: Iterate through the LIST
    for stream in data:
        # Ensure stream is a dictionary before processing
        if not isinstance(stream, dict):
            print(f"Warning: Skipping non-dictionary item in list: {stream}")
            continue

        # --- A. BUILD #EXTINF LINE ---
        # (Assuming original keys are now correct)
        extinf_parts = ["#EXTINF:-1"]
        
        if stream.get('channel_id'):
            extinf_parts.append(f'tvg-id="{stream["channel_id"]}"')
        if stream.get('channel_genre'):
            extinf_parts.append(f'group-title="{stream["channel_genre"]}"')
        if stream.get('channel_logo'):
            extinf_parts.append(f'tvg-logo="{stream["channel_logo"]}"')
        
        channel_name = stream.get('channel_name', 'Unknown Channel')
        
        extinf_line = " ".join(extinf_parts) + f",{channel_name}"
        m3u_lines.append(extinf_line)
        
        # --- B. ADD CUSTOM KODIPROP & HTTP TAGS ---
        # (Assuming original keys 'keyId' and 'key' are correct)
        
        key_id = stream.get('keyId') # Using 'keyId'
        key = stream.get('key')
        
        if key_id and key:
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_type=clearkey')
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}')

        m3u_lines.append(f'#EXTVLCOPT:http-user-agent=plaYtv/7.1.3 (Linux;Android 13) ygx/69.1 ExoPlayerLib/824.0')
        
        cookie_value = stream.get('cookie')
        if cookie_value:
            m3u_lines.append(f'#EXTHTTP:{{"cookie":"{cookie_value}"}}')
            
        # 4. Add the stream URL
        # (Assuming original key 'channel_url' is correct)
        stream_url = stream.get('channel_url', '') # Using 'channel_url'
        m3u_lines.append(stream_url)

    # 5. Write the M3U file
    try:
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines) + '\n')
        print(f"✅ Successfully converted {len(data)} streams to {OUTPUT_FILE_NAME}")
    except IOError as e:
        print(f"Error writing to output file {OUTPUT_FILE_NAME}: {e}")
        sys.exit(1)

def main():
    url = os.getenv('JSON_SOURCE_URL')
    if not url:
        print("Fatal Error: JSON_SOURCE_URL environment variable is not set.")
        sys.exit(1)
        
    data = fetch_data(url)
    json_to_m3u(data)

if __name__ == "__main__":
    main()
