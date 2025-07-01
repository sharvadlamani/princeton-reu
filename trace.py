#!/usr/bin/env python3
import os
import csv
import time
import requests
import socket
from scapy.all import IP, UDP, sr1
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading

asn_cache = {}
lock = threading.Lock()  # To protect CSV writer access

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

def read_domains_from_csv():
    domains = []
    with open("top-1m.csv", newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader):
            if i < 500 or (10000 <= i < 10500):
                domain = row[1].strip() if len(row) > 1 else row[0].strip()
                domains.append(domain)
            if i >= 10500:
                break
    return domains

def traceroute(destination, max_hops=30, timeout=2, writer=None, probes_per_hop=3):
    try:
        destination_ip = socket.gethostbyname(destination)
    except socket.gaierror:
        with lock:
            print(f"Could not resolve {destination}, skipping.")
            writer.writerow([destination, "N/A", "N/A", "Unresolvable", "", "", "", "", "", "", "", "", "", ""])
        return

    port = 33434
    ttl = 1
    any_response = False

    print(f"\nTraceroute to {destination} [{destination_ip}] (max hops: {max_hops}, timeout: {timeout}s):")
    print("".join([
        "Dest".ljust(30), "Hop".ljust(5), "Responder IP".ljust(20),
        "Org (ASN)".ljust(35), "RTT1".ljust(10), "RTT2".ljust(10), "RTT3".ljust(10)
    ]))

    while ttl <= max_hops:
        rtts = []
        responder_ip = None
        responder_info = {}
        reply = None

        for _ in range(probes_per_hop):
            ip_packet = IP(dst=destination_ip, ttl=ttl)
            udp_packet = UDP(dport=port)
            packet = ip_packet / udp_packet

            reply = sr1(packet, timeout=timeout, verbose=0)

            if reply:
                any_response = True
                try:
                    rtt = round((reply.time - packet.sent_time) * 1000, 2)
                except AttributeError:
                    rtt = "*"
                if not responder_ip:
                    responder_ip = reply.src
                    responder_info = get_as_info(responder_ip)
                rtts.append(rtt)
            else:
                rtts.append("*")

        org_display = responder_info.get("org", "N/A") if responder_ip else ""
        rtt_strs = [(f"{x} ms" if isinstance(x, float) else "*") for x in rtts]

        with lock:
            print("".join([
                destination.ljust(30),
                str(ttl).ljust(5),
                (responder_ip or "*").ljust(20),
                org_display.ljust(35),
                rtt_strs[0].ljust(10),
                rtt_strs[1].ljust(10),
                rtt_strs[2].ljust(10)
            ]))

            writer.writerow([
                destination,
                destination_ip,
                ttl,
                responder_ip or "*",
                org_display,
                responder_info.get("city", ""),
                responder_info.get("region", ""),
                responder_info.get("country", ""),
                responder_info.get("loc", ""),
                responder_info.get("postal", ""),
                responder_info.get("timezone", ""),
                rtts[0] if isinstance(rtts[0], float) else "*",
                rtts[1] if isinstance(rtts[1], float) else "*",
                rtts[2] if isinstance(rtts[2], float) else "*"
            ])

        if reply and reply.type == 3:
            break

        ttl += 1

    if not any_response:
        with lock:
            writer.writerow([
                destination, destination_ip, "N/A", "All hops timeout", "", "", "", "", "", "", "", "", "", ""
            ])

def main():
    parser = argparse.ArgumentParser(description="Traceroute to multiple destinations with ASN info and RTTs.")
    parser.add_argument("-m", "--max-hops", type=int, default=30, help="Maximum number of hops (default: 30)")
    parser.add_argument("-t", "--timeout", type=int, default=2, help="Timeout per hop in seconds (default: 2)")
    parser.add_argument("-j", "--threads", type=int, default=50, help="Number of threads (default: 50)")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="Delay between thread submissions (default: 0.1s)")
    args = parser.parse_args()

    domains = read_domains_from_csv()

    with open("traceroute_log_rtt.csv", mode="w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "Destination", "Destination IP", "Hop", "IP", "ASN", "City", "Region",
            "Country", "Loc", "Postal", "Timezone", "RTT1", "RTT2", "RTT3"
        ])

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = []
            for site in domains:
                futures.append(executor.submit(traceroute, site, args.max_hops, args.timeout, csv_writer))
                time.sleep(args.delay)

            # Optional: wait for all to complete
            for future in futures:
                future.result()

if __name__ == "__main__":
    main()

