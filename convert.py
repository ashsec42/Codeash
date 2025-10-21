# convert.py (WITH THREADING FOR SPEED)

import json
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_FILE_NAME = "playlist.m3u"
EPG_URL = "https://avkb.short.gy/jioepg.xml.gz"
MAX_WORKERS = 10  # Check 10 streams concurrently

# --- Function for thread workers ---
def check_stream_status(stream):
    """
    Checks if a stream URL explicitly returns HTTP 404 (Not Found).
    Returns the stream object if it's NOT a 404, or None if it is.
    """
    url = stream.get('channel_url', '')
    if not url:
        return None # Skip if URL is missing
    
    try:
        # Use HEAD request with a fast timeout (2 seconds)
        response = requests.head(url, timeout=2, allow_redirects=True)
        
        # We only remove streams that are explicitly 404 Not Found.
        if response.status_code == 404:
            print(f"❌ Removing {stream.get('channel_name', 'Unknown')}: Link returned HTTP 404.")
            return None # Dead link
        
        # Keep all other streams (2xx success, or 403 geo-blocked)
        return stream
        
    except requests.exceptions.RequestException:
        # Assume connection errors (timeouts/DNS) are due to geo-blocking or network lag.
        # We keep the stream, assuming it works on the user's device.
        return stream

# --- Main Conversion Logic ---
def json_to_m3u(json_url):
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

    # Use ThreadPoolExecutor to run checks in parallel
    working_streams = []
    print(f"Starting parallel check of {len(data)} streams...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all stream checks to the thread pool
        future_to_stream = {executor.submit(check_stream_status, stream): stream for stream in data}
        
        # Collect results as they complete
        for future in as_completed(future_to_stream):
            result = future.result()
            if result:
                working_streams.append(result)

    # 1. Start the M3U content with headers
    m3u_lines = [
        "#EXTM3U",
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]
    
    # 2. Build M3U lines from the filtered list
    for stream in working_streams:
        # --- A. BUILD #EXTINF LINE ---
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
        key_id = stream.get('keyId')
        key = stream.get('key')
        if key_id and key:
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_type=clearkey')
            m3u_lines.append(f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}')

        m3u_lines.append(f'#EXTVLCOPT:http-user-agent=plaYtv/7.1.3 (Linux;Android 13) ygx/69.1 ExoPlayerLib/824.0')
        
        cookie_value = stream.get('cookie')
        if cookie_value:
            m3u_lines.append(f'#EXTHTTP:{{"cookie":"{cookie_value}"}}')
            
        stream_url = stream.get('channel_url', '')
        m3u_lines.append(stream_url)

    # 3. Write the M3U file
    try:
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines) + '\n')
        print(f"✅ Conversion complete. Wrote {len(working_streams)} streams to {OUTPUT_FILE_NAME}")
    except IOError as e:
        print(f"Error writing to output file {OUTPUT_FILE_NAME}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    url = os.getenv('JSON_SOURCE_URL')
    if not url:
        print("Fatal Error: JSON_SOURCE_URL environment variable is not set.")
        sys.exit(1)
        
    json_to_m3u(url)
