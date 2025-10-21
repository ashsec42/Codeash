# convert.py (CORRECTED for your JSON structure)

import json
import os
import sys
import requests

# Define the output file name
OUTPUT_FILE_NAME = "playlist.m3u"

def json_to_m3u(json_url):
    """
    Fetches JSON from a URL and converts the data into an extended M3U file.
    Updated to handle keys: channel_name, channel_url, channel_logo, channel_genre, channel_id.
    """
    
    print(f"Fetching data from URL...")
    try:
        # 1. Fetch data from the secret URL
        response = requests.get(json_url, timeout=15)
        response.raise_for_status() # Check for bad status codes (4xx/5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching or decoding JSON: {e}")
        sys.exit(1)
        
    if not isinstance(data, list):
        print("Error: JSON root must be a list of stream objects. Check your JSON format.")
        sys.exit(1)

    # 2. Start the M3U content
    m3u_lines = ["#EXTM3U"]
    
    # 3. Process each stream object
    for stream in data:
        # Build the #EXTINF line (duration is typically -1 for live/indefinite)
        extinf_parts = ["#EXTINF:-1"]
        
        # --- MAPPING YOUR JSON KEYS TO M3U ATTRIBUTES ---

        # 1. Map 'channel_id' to 'tvg-id'
        if stream.get('channel_id'):
            extinf_parts.append(f'tvg-id="{stream["channel_id"]}"')
            
        # 2. Map 'channel_logo' to 'tvg-logo'
        if stream.get('channel_logo'):
            extinf_parts.append(f'tvg-logo="{stream["channel_logo"]}"')
        
        # 3. Map 'channel_genre' to 'group-title'
        if stream.get('channel_genre'):
            extinf_parts.append(f'group-title="{stream["channel_genre"]}"')
        
        # Get the Channel Name for the end of the line (using 'Unknown Channel' as fallback)
        channel_name = stream.get('channel_name', 'Unknown Channel')
        
        # Finalize the EXTINF line
        extinf_line = " ".join(extinf_parts) + f",{channel_name}"
        m3u_lines.append(extinf_line)
        
        # 4. Add the stream URL (must be on the next line)
        stream_url = stream.get('channel_url', '')
        m3u_lines.append(stream_url)

    # 5. Write the M3U file
    try:
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines) + '\n')
        print(f"✅ Successfully converted {len(data)} streams to {OUTPUT_FILE_NAME}")
    except IOError as e:
        print(f"Error writing to output file {OUTPUT_FILE_NAME}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get the secret URL from the GitHub Actions environment variable
    url = os.getenv('JSON_SOURCE_URL')
    if not url:
        print("Fatal Error: JSON_SOURCE_URL environment variable is not set.")
        sys.exit(1)
        
    json_to_m3u(url)
