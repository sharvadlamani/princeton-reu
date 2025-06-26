#!/usr/bin/env python3
import os
import sys
import csv
import requests
import socket
from scapy.all import IP, UDP, sr1
import argparse

asn_cache = {}

# --- Create CSV file and write header ---
csv_file = open("traceroute_log4.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Hop", "IP", "ASN", "City", "Region", "Country", "Loc", "Postal", "Timezone"])

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

def traceroute(destination, max_hops=30, timeout=2):
    port = 33434
    ttl = 1

    while True:
        ip_packet = IP(dst=destination, ttl=ttl)
        udp_packet = UDP(dport=port)
        packet = ip_packet / udp_packet
        reply = sr1(packet, timeout=timeout, verbose=0)

        if reply is None:
            print(f"{ttl}\t*\t*")
            csv_writer.writerow([ttl, "*", "", "", "", "", "", "", ""])
        else:
            ip = reply.src
            info = get_as_info(ip)

            # Terminal output (only 3 fields)
            print(f"{ttl}\t{ip}\t{info.get('org', 'N/A')}")

            # CSV output (all fields)
            csv_writer.writerow([
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
    parser = argparse.ArgumentParser(description="Traceroute with full ASN info in CSV, 3-field terminal output.")
    parser.add_argument("destination", help="Destination host or IP address.")
    parser.add_argument("-m", "--max-hops", type=int, default=30, help="Maximum number of hops (default: 30).")
    parser.add_argument("-t", "--timeout", type=int, default=2, help="Timeout for each packet in seconds (default: 2).")

    args = parser.parse_args()

    print(f"Traceroute to {args.destination} (max hops: {args.max_hops}, timeout: {args.timeout} seconds):")
    traceroute(args.destination, max_hops=args.max_hops, timeout=args.timeout)
    csv_file.close()

if __name__ == "__main__":
    main()

