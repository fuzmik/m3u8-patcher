import sys
import requests
import xml.etree.ElementTree as ET
import re
import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_channel_name(channel_name: str) -> str:
    """
    Normalize the channel name by removing '4k' and 'hd' tags, and converting it to lowercase.
    
    Args:
        channel_name (str): The original channel name.
    
    Returns:
        str: The normalized channel name.
    """
    return re.sub(r'\s*\(?4k\)?\s*|\s*\(?hd\)?\s*', '', channel_name.lower())

def update_url_tvg(playlist_lines: List[str], new_url: str) -> None:
    """
    Update the `url-tvg` attribute in the playlist's #EXTM3U line.
    
    Args:
        playlist_lines (List[str]): The lines of the playlist file.
        new_url (str): The new URL to add to the `url-tvg` attribute.
    """
    for i, line in enumerate(playlist_lines):
        if line.startswith("#EXTM3U"):
            current_url_tvg_match = re.search(r'url-tvg="([^"]*)"', line)
            if current_url_tvg_match:
                current_url_tvg = current_url_tvg_match.group(1)
                if new_url in current_url_tvg:
                    return
                new_url_tvg = f'{current_url_tvg}; {new_url}' if current_url_tvg else new_url
                playlist_lines[i] = re.sub(r'url-tvg="[^"]*"', f'url-tvg="{new_url_tvg}"', line)
            else:
                playlist_lines[i] = line.rstrip() + f' url-tvg="{new_url}"\n'
            break

def fetch_epg(epg_url: str) -> List[Dict[str, str]]:
    """
    Fetch and parse the EPG XML from the given URL.
    
    Args:
        epg_url (str): The URL of the EPG XML file.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing channel names and their corresponding `tvg-id`s.
    """
    response = requests.get(epg_url)
    response.raise_for_status()
    epg_content = response.text.replace('&', '&amp;')

    channels = []
    root = ET.fromstring(epg_content)
    for channel in root.findall('channel'):
        tvg_id = channel.get('id')
        display_name = None
        for name_tag in channel.findall('display-name'):
            if name_tag.attrib.get('lang') == 'en':
                display_name = name_tag.text
                break
        if not display_name:
            display_name = channel.find('display-name').text if channel.find('display-name') is not None else None
        if tvg_id and display_name:
            channels.append({'channelName': display_name, 'tvgId': tvg_id})
    return channels

def update_playlist(playlist_lines: List[str], channels: List[Dict[str, str]], epg_url: str) -> List[str]:
    """
    Update the playlist with `tvg-id`, `tvg-chno`, `tvg-name`, `tvg-logo`, `tvg-url`, `TVG-EPGSHIFT`, `TVG-EPGURL`, and `tvg-epgid` attributes for each channel.
    If the tags are missing or empty, update them with the values from the channels list.
    If the tags are already set, skip updating them.
    
    Args:
        playlist_lines (List[str]): The lines of the playlist file.
        channels (List[Dict[str, str]]): A list of dictionaries containing channel names and their corresponding `tvg-id`s.
        epg_url (str): The URL of the EPG XML file.
    
    Returns:
        List[str]: The updated lines of the playlist file.
    """
    updated_playlist_lines = []
    for line in playlist_lines:
        if line.startswith("#EXTINF"):
            matched = False
            for channel in channels:
                normalized_channel_name = normalize_channel_name(channel['channelName'])
                normalized_line = normalize_channel_name(line)
                if normalized_channel_name in normalized_line or normalized_channel_name.replace('channel', 'ch') in normalized_line.replace('channel', 'ch'):
                    # Check and update tvg-id if missing or empty
                    if 'tvg-id="' not in line or re.search(r'tvg-id=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-id="{channel["tvgId"]}"', line, count=1)
                    # Check and update tvg-chno if missing or empty
                    if 'tvg-chno="' not in line or re.search(r'tvg-chno=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-chno="{channel.get("tvgChno", "unknown")}"', line, count=1)
                    # Check and update tvg-name if missing or empty
                    if 'tvg-name="' not in line or re.search(r'tvg-name=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-name="{channel["channelName"]}"', line, count=1)
                    # Check and update tvg-logo if missing or empty
                    if 'tvg-logo="' not in line or re.search(r'tvg-logo=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-logo="{channel.get("tvgLogo", "unknown")}"', line, count=1)
                    # Check and update tvg-url if missing or empty
                    if 'tvg-url="' not in line or re.search(r'tvg-url=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-url="{channel.get("tvgUrl", "unknown")}"', line, count=1)
                    # Check and update TVG-EPGSHIFT if missing or empty
                    if 'TVG-EPGSHIFT="' not in line or re.search(r'TVG-EPGSHIFT=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 TVG-EPGSHIFT="{channel.get("TVG-EPGSHIFT", "unknown")}"', line, count=1)
                    # Check and update TVG-EPGURL if missing or empty
                    if 'TVG-EPGURL="' not in line or re.search(r'TVG-EPGURL=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 TVG-EPGURL="{channel.get("TVG-EPGURL", "unknown")}"', line, count=1)
                    # Check and update tvg-epgid if missing or empty
                    if 'tvg-epgid="' not in line or re.search(r'tvg-epgid=""', line):
                        line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-epgid="{channel.get("tvgEpgid", "unknown")}"', line, count=1)
                    matched = True
                    break
            if not matched:
                if 'tvg-id="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-id="unknown"', line, count=1)
                if 'tvg-chno="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-chno="unknown"', line, count=1)
                if 'tvg-name="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-name="unknown"', line, count=1)
                if 'tvg-logo="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-logo="unknown"', line, count=1)
                if 'tvg-url="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-url="unknown"', line, count=1)
                if 'TVG-EPGSHIFT="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 TVG-EPGSHIFT="unknown"', line, count=1)
                if 'TVG-EPGURL="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 TVG-EPGURL="unknown"', line, count=1)
                if 'tvg-epgid="' not in line:
                    line = re.sub(r'(#EXTINF[^,]*,)', f'\\1 tvg-epgid="unknown"', line, count=1)
        updated_playlist_lines.append(line)

    # Ensure url-tvg is present in the #EXTM3U line
    if not any(line.startswith("#EXTM3U") and 'url-tvg="' in line for line in updated_playlist_lines):
        for i, line in enumerate(updated_playlist_lines):
            if line.startswith("#EXTM3U"):
                updated_playlist_lines[i] = line.rstrip() + f' url-tvg="{epg_url}"\n'
                break

    return updated_playlist_lines

def main(playlist_file: str, epg_url: str) -> None:
    """
    Main function to patch the playlist file with new `tvg-id` and `tvg-name` values and `url-tvg`.
    
    Args:
        playlist_file (str): The path to the playlist file.
        epg_url (str): The URL of the EPG XML file.
    """
    try:
        with open(playlist_file, 'r') as file:
            playlist_lines = file.readlines()

        channels = fetch_epg(epg_url)
        update_url_tvg(playlist_lines, epg_url)
        updated_playlist_lines = update_playlist(playlist_lines, channels, epg_url)

        with open(playlist_file, 'w') as file:
            file.writelines(updated_playlist_lines)

        logging.info(f"Patched '{playlist_file}' with new tvg-id and tvg-name values and url-tvg.")

    except FileNotFoundError:
        logging.error(f"The file '{playlist_file}' does not exist.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching EPG URL: {e}")
    except ET.ParseError:
        logging.error("Failed to parse the EPG XML.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Usage: python script.py playlist.m3u8 \"http://example.com/epg.xml\"")
        sys.exit(1)

    playlist_file = sys.argv[1]
    epg_url = sys.argv[2]
    main(playlist_file, epg_url)
