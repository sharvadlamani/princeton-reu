#!/usr/bin/env python3
import os
import csv
import requests
import socket
from scapy.all import IP, UDP, sr1
import argparse

asn_cache = {}

# Website list (hardcoded)
destinations = [
    "google.com", "mail.ru", "microsoft.com", "facebook.com", "apple.com",
    "amazonaws.com", "dzen.ru", "youtube.com", "googleapis.com", "cloudflare.com",
    "akamai.net", "instagram.com", "twitter.com", "akamaiedge.net", "office.com",
    "gstatic.com", "azure.com", "linkedin.com", "live.com", "akadns.net",
    "googlevideo.com", "ax-msedge.net", "googletagmanager.com", "fbcdn.net",
    "apple-dns.net", "windowsupdate.com", "amazon.com", "workers.dev",
    "wikipedia.org", "microsoftonline.com"
]

def get_as_info(ip):
    if ip in asn_cache:
        return asn_cache[ip]
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        data = response.json()
        asn_cache[ip] = data
        return data
    except Exception:
        return {}

def traceroute(destination, max_hops=30, timeout=2, writer=None):
    try:
        socket.gethostbyname(destination)
    except socket.gaierror:
        print(f"⚠️ Could not resolve {destination}, skipping.")
        writer.writerow([destination, "N/A", "N/A", "Unresolvable", "", "", "", "", "", ""])
        return

    port = 33434
    ttl = 1

    print(f"\nTraceroute to {destination} (max hops: {max_hops}, timeout: {timeout}s):")
    while True:
        ip_packet = IP(dst=destination, ttl=ttl)
        udp_packet = UDP(dport=port)
        packet = ip_packet / udp_packet
        reply = sr1(packet, timeout=timeout, verbose=0)

        if reply is None:
            print(f"{ttl}\t*\t*")
            writer.writerow([destination, ttl, "*", "", "", "", "", "", "", ""])
        else:
            ip = reply.src
            info = get_as_info(ip)
            print(f"{ttl}\t{ip}\t{info.get('org', 'N/A')}")
            writer.writerow([
                destination,
                ttl,
                ip,
                info.get("org", ""),
                info.get("city", ""),
                info.get("region", ""),
                info.get("country", ""),
                info.get("loc", ""),
                info.get("postal", ""),
                info.get("timezone", "")
            ])
            if reply.type == 3:
                break
        ttl += 1
        if ttl > max_hops:
            break

def main():
    parser = argparse.ArgumentParser(description="Traceroute to multiple destinations with ASN info.")
    parser.add_argument("-m", "--max-hops", type=int, default=30, help="Maximum number of hops (default: 30)")
    parser.add_argument("-t", "--timeout", type=int, default=2, help="Timeout per hop in seconds (default: 2)")
    args = parser.parse_args()

    with open("traceroute_log_all.csv", mode="w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "Destination", "Hop", "IP", "ASN", "City", "Region",
            "Country", "Loc", "Postal", "Timezone"
        ])
        for site in destinations:
            traceroute(site, max_hops=args.max_hops, timeout=args.timeout, writer=csv_writer)

if __name__ == "__main__":
    main()

