# convert.py

import json
import os
import sys
import requests

# Define the output file name
OUTPUT_FILE_NAME = "playlist.m3u"

def json_to_m3u(json_url):
    """
    Fetches JSON from a URL and converts the data into an extended M3U file.
    It expects a JSON array of objects, each containing 'name', 'url', and attributes.
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
        
        # Add M3U attributes (Customize these keys to match your JSON data fields)
        if stream.get('tvg-id'):
            extinf_parts.append(f'tvg-id="{stream["tvg-id"]}"')
        if stream.get('group-title'):
            extinf_parts.append(f'group-title="{stream["group-title"]}"')
        if stream.get('logo'): 
            extinf_parts.append(f'tvg-logo="{stream["logo"]}"')
        
        # Finalize the EXTINF line with the stream name
        channel_name = stream.get('name', 'Unknown Channel')
        extinf_line = " ".join(extinf_parts) + f",{channel_name}"
        m3u_lines.append(extinf_line)
        
        # 4. Add the stream URL (must be on the next line)
        m3u_lines.append(stream.get('url', ''))

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
        print("Ensure you have set this secret in your GitHub repository settings.")
        sys.exit(1)
        
    json_to_m3u(url)
