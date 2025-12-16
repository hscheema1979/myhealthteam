import requests
import logging
import sys
import time

# --- CONFIGURATION ---
# Get your API Token from: https://hpanel.hostinger.com/profile/api-tokens
# Ensure the token has 'DNS Zones' permission.
API_TOKEN = "YOUR_HOSTINGER_API_TOKEN_HERE"
DOMAIN = "myhealthteam.org"
RECORD_NAME = "care"  # The subdomain to update
RECORD_TYPE = "A"

# --- CONSTANTS ---
HOSTINGER_API_URL = "https://api.hostinger.com/v1"
IPIFY_URL = "https://api.ipify.org"

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("dns_update.log")
    ]
)
logger = logging.getLogger()

def get_public_ip():
    """Fetches the current public IP address."""
    try:
        response = requests.get(IPIFY_URL, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        logger.error(f"Failed to get public IP: {e}")
        return None

def get_dns_records(domain):
    """Fetches all DNS records for the domain."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{HOSTINGER_API_URL}/dns/zones/{domain}/records"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException as e:
        logger.error(f"Failed to fetch DNS records: {e}")
        if response.status_code == 401:
            logger.error("Authentication failed. Check your API Token.")
        return None

def update_dns_record(domain, record_id, new_ip):
    """Updates a specific DNS record."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{HOSTINGER_API_URL}/dns/zones/{domain}/records/{record_id}"
    payload = {
        "content": new_ip,
        "ttl": 300,
        "type": "A",
        "name": RECORD_NAME
    }
    
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully updated DNS record to {new_ip}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to update DNS record: {e}")
        logger.error(f"Response: {response.text}")
        return False

def main():
    if API_TOKEN == "YOUR_HOSTINGER_API_TOKEN_HERE":
        logger.error("Please configure your API_TOKEN in the script.")
        return

    # 1. Get Public IP
    current_ip = get_public_ip()
    if not current_ip:
        return

    logger.info(f"Current Public IP: {current_ip}")

    # 2. Get Hostinger Records
    records = get_dns_records(DOMAIN)
    if not records:
        return

    # 3. Find the target record
    target_record = None
    for record in records:
        if record['type'] == RECORD_TYPE and record['name'] == RECORD_NAME:
            target_record = record
            break
    
    if not target_record:
        logger.error(f"Record {RECORD_NAME}.{DOMAIN} (Type: {RECORD_TYPE}) not found.")
        return

    # 4. Compare and Update
    dns_ip = target_record['content']
    record_id = target_record['id']
    
    logger.info(f"Current DNS IP: {dns_ip}")

    if current_ip != dns_ip:
        logger.info("IP mismatch detected. Updating DNS...")
        update_dns_record(DOMAIN, record_id, current_ip)
    else:
        logger.info("IPs match. No update needed.")

if __name__ == "__main__":
    main()
