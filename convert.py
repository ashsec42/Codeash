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
    Converts the JSON (as an object) into a detailed M3U format.
    """
    
    # 1. NEW: Check if the JSON root is an OBJECT (a dict)
    if not isinstance(data, dict):
        print(f"Error: JSON root must be an object (dictionary). Got: {type(data)}")
        print("This script is designed for the key-value JSON structure you provided.")
        sys.exit(1)

    print(f"Successfully fetched {len(data)} stream objects (as an object). Converting...")

    m3u_lines = [
        "#EXTM3U",
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]
    
    # 2. NEW: Iterate using .items() to get BOTH the channel ID and the stream data
    for channel_id, stream in data.items():
        
        # --- A. BUILD #EXTINF LINE ---
        extinf_parts = ["#EXTINF:-1"]
        
        # Use the JSON key (e.g., "143") as the tvg-id
        extinf_parts.append(f'tvg-id="{channel_id}"')
        
        # NOTE: Your new JSON has no 'channel_name', 'channel_genre', or 'channel_logo'.
        # We will use the channel_id as a stand-in for the name.
        # You may need to find another source for this metadata.
        channel_name = f"Channel {channel_id}"
        
        extinf_line = " ".join(extinf_parts) + f",{channel_name}"
        m3u_lines.append(extinf_line)
        
        # --- B. ADD CUSTOM KODIPROP & HTTP TAGS (with remapped keys) ---
        
        # REMAPPED: 'keyId' -> 'kid'
        key_id = stream.get('kid') 
        key = stream.get('key')
        
        if key_id and key:
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_type=clearkey')
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}')

        m3u_lines.append(f'#EXTVLCOPT:http-user-agent=plaYtv/7.1.3 (Linux;Android 13) ygx/69.1 ExoPlayerLib/824.0')
        
        # Your new JSON doesn't have 'cookie', but we leave the logic
        # in case some streams have it.
        cookie_value = stream.get('cookie')
        if cookie_value:
            m3u_lines.append(f'#EXTHTTP:{{"cookie":"{cookie_value}"}}')
            
        # 4. Add the stream URL
        # REMAPPED: 'channel_url' -> 'url'
        stream_url = stream.get('url', '') 
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
