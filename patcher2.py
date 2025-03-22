import sys
import requests
import xml.etree.ElementTree as ET
import re
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_channel_name(channel_name: str) -> str:
    """Normalizes the channel name by removing common HD/4K tags and lowercase."""
    return re.sub(r'\s*\(?(?:hd|4k)\)?\s*', '', channel_name.lower())

def update_url_tvg(playlist_lines: List[str], new_url: str) -> None:
    """Updates the url-tvg attribute in the #EXTM3U line with the new EPG URL."""
    new_url = new_url.strip()
    for i, line in enumerate(playlist_lines):
        if line.startswith("#EXTM3U"):
            current_url_tvg_match = re.search(r'url-tvg="([^"]*)"', line)
            if current_url_tvg_match:
                current_urls = [url.strip() for url in current_url_tvg_match.group(1).split(';')]
                if new_url in current_urls:
                    return
                current_urls.append(new_url)
                new_url_tvg = '; '.join(current_urls)
                playlist_lines[i] = re.sub(r'url-tvg="[^"]*"', f'url-tvg="{new_url_tvg}"', line)
            else:
                playlist_lines[i] = line.rstrip() + f' url-tvg="{new_url}"\n'
            break

def fetch_epg(epg_url: str) -> List[Dict[str, str]]:
    """Fetches and parses the EPG XML to extract channel data."""
    try:
        response = requests.get(epg_url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        channels = []
        for channel in root.findall('channel'):
            tvg_id = channel.get('id')
            display_name = None
            for name_tag in channel.findall('display-name'):
                if name_tag.attrib.get('lang', 'en') == 'en':
                    display_name = name_tag.text
                    break
            if not display_name and channel.find('display-name') is not None:
                display_name = channel.find('display-name').text
            if tvg_id and display_name:
                channels.append({'channelName': display_name.strip(), 'tvgId': tvg_id})
        return channels
    except ET.ParseError as e:
        logging.error(f"XML parsing error: {e}")
        raise

def update_playlist(playlist_lines: List[str], channels: List[Dict[str, str]], epg_url: str) -> List[str]:
    """Updates the playlist with tvg-id and tvg-name based on EPG data."""
    updated_lines = []
    for line in playlist_lines:
        if line.startswith("#EXTINF"):
            parts = line.strip().split(',', 1)
            if len(parts) < 2:
                updated_lines.append(line)
                continue
            header, display_name = parts
            display_name = display_name.strip()
            normalized_display = normalize_channel_name(display_name)
            matched = False
            for channel in channels:
                epg_name = normalize_channel_name(channel['channelName'])
                if epg_name == normalized_display:
                    new_header = header
                    # Update tvg-id
                    if 'tvg-id=' in new_header:
                        new_header = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{channel["tvgId"]}"', new_header)
                    else:
                        new_header += f' tvg-id="{channel["tvgId"]}"'
                    # Update tvg-name
                    if 'tvg-name=' in new_header:
                        new_header = re.sub(r'tvg-name="[^"]*"', f'tvg-name="{channel["channelName"]}"', new_header)
                    else:
                        new_header += f' tvg-name="{channel["channelName"]}"'
                    line = f"{new_header},{display_name}\n"
                    matched = True
                    break
            if not matched:
                new_header = header
                if 'tvg-id=' not in new_header:
                    new_header += ' tvg-id="unknown"'
                if 'tvg-name=' not in new_header:
                    new_header += ' tvg-name="unknown"'
                line = f"{new_header},{display_name}\n"
        updated_lines.append(line)
    # Ensure url-tvg is present
    extm3u_found = False
    for i, line in enumerate(updated_lines):
        if line.startswith("#EXTM3U"):
            if 'url-tvg=' not in line:
                updated_lines[i] = re.sub(r'(#EXTM3U.*?)(\s*)$', rf'\1 url-tvg="{epg_url}"\2', line).strip() + '\n'
            extm3u_found = True
            break
    if not extm3u_found and updated_lines:
        updated_lines.insert(0, f'#EXTM3U url-tvg="{epg_url}"\n')
    return updated_lines

def main(playlist_file: str, epg_url: str) -> None:
    try:
        with open(playlist_file, 'r') as f:
            playlist_lines = f.readlines()
        channels = fetch_epg(epg_url)
        update_url_tvg(playlist_lines, epg_url)
        updated_playlist = update_playlist(playlist_lines, channels, epg_url)
        with open(playlist_file, 'w') as f:
            f.writelines(updated_playlist)
        logging.info(f"Successfully updated '{playlist_file}' with EPG data from {epg_url}.")
    except Exception as e:
        logging.error(f"Error processing playlist: {e}", exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <playlist.m3u> <epg_url>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
