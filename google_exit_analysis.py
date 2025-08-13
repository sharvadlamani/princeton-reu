import os
import pandas as pd
import re
from statistics import median
from geopy.distance import geodesic
import ipaddress

# GCP region → coordinates mapping
gcp_coords = {
    "africa-south1": (-26.2041, 28.0473),
    "asia-east1": (24.0728, 120.5400),
    "asia-east2": (22.3193, 114.1694),
    "asia-northeast1": (35.6762, 139.6503),
    "asia-northeast2": (34.6937, 135.5023),
    "asia-northeast3": (37.5665, 126.9780),
    "asia-south1": (19.0760, 72.8777),
    "asia-south2": (28.6139, 77.2090),
    "asia-southeast1": (1.3483, 103.7042),
    "asia-southeast2": (-6.2088, 106.8456),
    "australia-southeast1": (-33.8688, 151.2093),
    "australia-southeast2": (-37.8136, 144.9631),
    "europe-central2": (52.2298, 21.0118),
    "europe-north1": (60.5667, 27.4167),
    "europe-southwest1": (40.4168, -3.7038),
    "europe-west1": (50.4267, 3.8314),
    "europe-west2": (51.5074, -0.1278),
    "europe-west3": (50.1109, 8.6821),
    "europe-west4": (53.4428, 6.8693),
    "europe-west6": (47.3769, 8.5417),
    "europe-west8": (45.4642, 9.1900),
    "europe-west9": (48.8566, 2.3522),
    "europe-west10": (52.5200, 13.4050),
    "europe-west12": (45.0703, 7.6869),
    "me-central1": (25.276987, 51.520008),
    "me-west1": (32.0853, 34.7818),
    "northamerica-northeast1": (45.5017, -73.5673),
    "northamerica-northeast2": (43.6517, -79.3832),
    "northamerica-south1": (20.5888, -100.3899),
    "southamerica-east1": (-23.5329, -46.7918),
    "southamerica-west1": (-33.4489, -70.6693),
    "us-central1": (41.2619, -95.8608),
    "us-east1": (33.1928, -80.0323),
    "us-east4": (39.0438, -77.4874),
    "us-east5": (39.9612, -82.9988),
    "us-south1": (32.7767, -96.7970),
    "us-west1": (45.5944, -121.1787),
    "us-west2": (34.0522, -118.2437),
    "us-west3": (40.7608, -111.8910),
    "us-west4": (36.1699, -115.1398)
}

google_ip_ranges = [
    "8.8.8.0/24", "8.34.208.0/20", "8.35.192.0/20", "35.190.0.0/17", "64.233.160.0/19",
    "66.102.0.0/20", "66.249.64.0/19", "72.14.192.0/18", "74.125.0.0/16", "108.177.0.0/17",
    "108.170.0.0/15", "108.172.0.0/14", "142.250.0.0/15", "172.217.0.0/16",
    "209.85.128.0/17", "216.58.192.0/19", "216.239.32.0/19"
]
google_networks = [ipaddress.IPv4Network(cidr) for cidr in google_ip_ranges]

def get_vm_coords(filename):
    match = re.search(r'vm-([a-z0-9\-]+)', filename)
    return gcp_coords.get(match.group(1)) if match else None

def is_google(asn, ip):
    asn_check = isinstance(asn, str) and ("google" in asn.lower() or "as15169" in asn.lower())
    ip_check = False
    try:
        ip_obj = ipaddress.ip_address(ip)
        ip_check = any(ip_obj in net for net in google_networks)
    except:
        pass
    return asn_check or ip_check

def distance_to_last_google(group, vm_coords):
    last_google = group[group["Is Google"]][::-1]
    for _, row in last_google.iterrows():
        loc = row.get("Loc")
        if isinstance(loc, str) and "," in loc:
            try:
                lat, lon = map(float, loc.strip().split(","))
                return geodesic(vm_coords, (lat, lon)).km
            except:
                pass
    return "N/A"

def analyze_file(filepath, output_path):
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    df['ASN'] = df['ASN'].astype(str).str.strip()
    df['Destination'] = df['Destination'].astype(str).str.strip()
    df['Source'] = df['Source'].astype(str).str.strip()
    for k in ['RTT1', 'RTT2', 'RTT3']:
        if k in df.columns:
            df[k] = pd.to_numeric(df[k], errors='coerce')
    df['Is Google'] = df.apply(lambda row: is_google(row['ASN'], row['IP']), axis=1)

    vm_coords = get_vm_coords(filepath)
    summary_rows = []

    for dest, group in df.groupby("Destination"):
        group = group.reset_index(drop=True)
        source_val = group.loc[0, "Source"] if "Source" in group.columns else "N/A"
        last_google_idx = group[group["Is Google"]].last_valid_index()

        if last_google_idx is None:
            summary_rows.append({
                "Destination": dest,
                "Source": source_val,
                "Median RTT to Last Google Node (ms)": "N/A",
                "Median RTT to Last Node (ms)": "N/A",
                "RTT Ratio (Google/Total)": "N/A",
                "RTT from Google Exit to Last Node (ms)": "N/A",
                "Exit Status": "google edge not detected",
                "Distance to Last Google Node (km)": "N/A",
                "Last Google IP": "N/A",
                "Last Google ASN": "N/A",
                "Hops Before Exit": 0
            })
            continue

        google_row = group.loc[last_google_idx]
        google_rtts = [google_row[k] for k in ['RTT1', 'RTT2', 'RTT3'] if pd.notnull(google_row[k]) and google_row[k] > 0]
        median_google_rtt = median(google_rtts) if google_rtts else "N/A"

        if last_google_idx == group.index[-1]:
            status = "last node was google"
        elif group.loc[last_google_idx + 1, "ASN"] == "*":
            status = "timeout"
        else:
            status = "exited google"

        median_final_rtt = "N/A"
        for i in range(len(group) - 1, -1, -1):
            row = group.iloc[i]
            rtts = [row[k] for k in ['RTT1', 'RTT2', 'RTT3'] if pd.notnull(row[k]) and row[k] > 0]
            if rtts:
                median_final_rtt = median(rtts)
                break

        if isinstance(median_google_rtt, (int, float)) and isinstance(median_final_rtt, (int, float)):
            rtt_diff = round(median_final_rtt - median_google_rtt, 3)
            ratio = round(median_google_rtt / median_final_rtt, 3) if median_final_rtt != 0 else "N/A"
        else:
            rtt_diff = "N/A"
            ratio = "N/A"

        summary_rows.append({
            "Destination": dest,
            "Source": source_val,
            "Median RTT to Last Google Node (ms)": median_google_rtt,
            "Median RTT to Last Node (ms)": median_final_rtt,
            "RTT Ratio (Google/Total)": ratio,
            "RTT from Google Exit to Last Node (ms)": rtt_diff,
            "Exit Status": status,
            "Distance to Last Google Node (km)": distance_to_last_google(group, vm_coords) if vm_coords else "N/A",
            "Last Google IP": google_row.get("IP", "N/A"),
            "Last Google ASN": google_row.get("ASN", "N/A"),
            "Hops Before Exit": last_google_idx + 1
        })

    pd.DataFrame(summary_rows).to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

base_dirs = {
    "premium": os.path.expanduser("~/reu/tofu-deployment-premium"),
    "standard": os.path.expanduser("~/reu/tofu-deployment-standard")
}

for tier, base_dir in base_dirs.items():
    input_dir = os.path.join(base_dir, "trimmed_traceroutes")
    output_dir = os.path.join(base_dir, "google_exit_analysis")
    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if fname.endswith(".csv"):
            in_path = os.path.join(input_dir, fname)
            out_path = os.path.join(output_dir, fname.replace(".csv", "_google_exit.csv"))
            analyze_file(in_path, out_path)

