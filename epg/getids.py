import requests
urls = [
    "https://epgshare01.online/epgshare01/epg_ripper_AR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_BEIN1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_BG1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_BR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_CA1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_CL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_CO1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_CR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_CY1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_DK1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_ES1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_FANDUEL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_FANDUEL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_FR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_GR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_IL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_IN4.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_MX1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_MY1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_NL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_NZ1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_PK1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_RO1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_RO2.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_SA1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_SE1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_TR1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_US1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS2.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_UY1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_ZA1.txt",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.txt",
]
combined_content = ""
for url in urls:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        content = response.text
        combined_content += content
        print(f"Successfully fetched content from: {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching content from {url}: {e}")
# Split the combined content into lines and filter out lines starting with "2025" or "--" and empty lines
lines = combined_content.splitlines()
filtered_lines = [line for line in lines if line.strip() and not line.startswith("2025") and not line.startswith("--")]
filtered_content = "\n".join(filtered_lines)
try:
    with open("tvg-ids-fetched.txt", "w", encoding="utf-8") as file:
        file.write(filtered_content)
    print("All content combined, filtered, and saved to tvg-ids-fetched.txt")
except Exception as e:
    print(f"Error saving to file: {e}")
