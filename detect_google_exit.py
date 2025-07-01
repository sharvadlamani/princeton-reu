import csv
from statistics import median
from collections import defaultdict

INPUT_CSV = "traceroute_log_rtt.csv"
OUTPUT_CSV = "google_exit_summary.csv"

def is_google_asn(asn_string):
    return "google" in asn_string.lower() or "as15169" in asn_string.lower()

def parse_median_rtt(row):
    rtts = []
    for key in ["RTT1", "RTT2", "RTT3"]:
        try:
            rtt = float(row[key])
            rtts.append(rtt)
        except (ValueError, TypeError):
            continue
    if rtts:
        return median(rtts)
    return None

def analyze_traces(input_file, output_file):
    with open(input_file, newline='') as csvfile:
        reader = list(csv.DictReader(csvfile))
        traces = defaultdict(list)

        for row in reader:
            traces[row['Destination']].append(row)

        with open(output_file, mode='w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow([
                "Destination",
                "Last Google Hop #",
                "Last Google IP",
                "Exit Hop #",
                "Exit IP",
                "Hops Before Exit",
                "Median RTT to Last Google Hop (ms)",
                "Status"
            ])

            for dest, hops in traces.items():
                last_google_hop = None
                last_google_ip = None
                last_google_rtt = None
                exit_hop = None
                exit_ip = None
                saw_non_google = False
                saw_star_after_google = False

                for row in hops:
                    hop = int(row['Hop']) if row['Hop'].isdigit() else None
                    ip = row['IP']
                    asn = row['ASN']

                    if ip == "*" or not ip:
                        if last_google_hop is not None and not saw_non_google:
                            saw_star_after_google = True
                        continue

                    if is_google_asn(asn):
                        last_google_hop = hop
                        last_google_ip = ip
                        last_google_rtt = parse_median_rtt(row)
                    elif last_google_hop is not None and not saw_non_google:
                        exit_hop = hop
                        exit_ip = ip
                        saw_non_google = True

                if last_google_hop:
                    if saw_star_after_google and not saw_non_google:
                        writer.writerow([
                            dest, last_google_hop, last_google_ip,
                            "", "", "", last_google_rtt, "Timeout after last Google hop"
                        ])
                    elif exit_hop:
                        writer.writerow([
                            dest, last_google_hop, last_google_ip,
                            exit_hop, exit_ip, exit_hop - 1,
                            last_google_rtt, "Exited Google"
                        ])
                    else:
                        writer.writerow([
                            dest, last_google_hop, last_google_ip,
                            "", "", "", last_google_rtt, "Unknown exit"
                        ])
                else:
                    writer.writerow([
                        dest, "", "", "", "", "", "", "No Google node found"
                    ])

    print(f"Summary written to {output_file}")

if __name__ == "__main__":
    analyze_traces(INPUT_CSV, OUTPUT_CSV)

