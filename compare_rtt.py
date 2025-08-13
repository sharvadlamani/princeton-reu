import os
import pandas as pd

# Paths to standard and premium output folders
std_dir = os.path.expanduser("~/reu/tofu-deployment-standard/google_exit_analysis")
prem_dir = os.path.expanduser("~/reu/tofu-deployment-premium/google_exit_analysis")

# Output text file
output_path = os.path.expanduser("~/reu/rtt_comparison_results.txt")

# Match using region key, strip known suffixes
std_files = {
    f.replace("_standard_trimmed_google_exit.csv", ""): os.path.join(std_dir, f)
    for f in os.listdir(std_dir) if f.endswith("_standard_trimmed_google_exit.csv")
}
prem_files = {
    f.replace("_premium_trimmed_google_exit.csv", ""): os.path.join(prem_dir, f)
    for f in os.listdir(prem_dir) if f.endswith("_premium_trimmed_google_exit.csv")
}

# Find common VMs
common_keys = sorted(set(std_files) & set(prem_files))
print(f"✅ Found {len(common_keys)} VM pairs to compare.")

# Store output lines
lines = [f"{'VM Region':<35} {'Total':<8} {'Premium < Std':<15} {'Percentage':<10}",
         "-" * 70]

for vm in common_keys:
    print(f"\n🔍 Comparing VM: {vm}")
    std_path = std_files[vm]
    prem_path = prem_files[vm]

    try:
        std_df = pd.read_csv(std_path)
        prem_df = pd.read_csv(prem_path)
        print(f"   ✅ Loaded: {os.path.basename(std_path)}, {os.path.basename(prem_path)}")
    except Exception as e:
        print(f"   ❌ Failed to load files for {vm}: {e}")
        continue

    # Filter for "exited google"
    std_df = std_df[std_df["Exit Status"] == "exited google"]
    prem_df = prem_df[prem_df["Exit Status"] == "exited google"]
    print(f"   📉 Filtered rows: {len(std_df)} (std), {len(prem_df)} (prem)")

    # Merge on Destination
    merged = pd.merge(
        std_df[["Destination", "Median RTT to Last Node (ms)"]],
        prem_df[["Destination", "Median RTT to Last Node (ms)"]],
        on="Destination",
        suffixes=("_std", "_prem")
    )

    print(f"   🔗 Matched destinations: {len(merged)}")

    # Convert to numeric and drop invalids
    merged["Median RTT to Last Node (ms)_std"] = pd.to_numeric(
        merged["Median RTT to Last Node (ms)_std"], errors="coerce")
    merged["Median RTT to Last Node (ms)_prem"] = pd.to_numeric(
        merged["Median RTT to Last Node (ms)_prem"], errors="coerce")
    merged = merged.dropna()

    total = len(merged)
    count = (merged["Median RTT to Last Node (ms)_prem"] <
             merged["Median RTT to Last Node (ms)_std"]).sum()
    pct = round((count / total) * 100, 2) if total > 0 else "N/A"

    print(f"   📊 Premium ≥ Std: {count}/{total} ({pct}%)")

    lines.append(f"{vm:<35} {total:<8} {count:<15} {pct if pct != 'N/A' else 'N/A':<10}")

# Save to file
with open(output_path, "w") as f:
    for line in lines:
        f.write(line + "\n")

print(f"\n✅ Results saved to: {output_path}")

