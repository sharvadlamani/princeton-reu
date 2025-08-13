import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import re

# Matplotlib style
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.family'] = 'serif'
plt.style.use('tableau-colorblind10')

def normalize_sources(df):
    df['Source Group'] = df['Source'].apply(
        lambda x: 'vultr*' if isinstance(x, str) and 'vultr' in x.lower()
        else x.lower().strip() if isinstance(x, str) and x.lower().strip() in ['tranco-top1k', 'tranco-rank10k', 'tranco-rank100k']
        else 'other'
    )
    return df

def extract_region(filename):
    match = re.search(r'vm-([a-z0-9\-]+)', filename)
    return match.group(1) if match else None

def compute_global_limits(std_files, prem_files, columns, source_groups):
    xlimits = {col: [np.inf, -np.inf] for col in columns}
    for file_dict in [std_files, prem_files]:
        for fpath in file_dict.values():
            df = normalize_sources(pd.read_csv(fpath))
            for col in columns:
                for group in source_groups:
                    vals = pd.to_numeric(df[df['Source Group'] == group][col], errors='coerce').dropna()
                    if col == "RTT Ratio (Google/Non-Google)":
                        vals = vals[vals <= 3]
                    if len(vals):
                        xlimits[col][0] = min(xlimits[col][0], vals.min())
                        xlimits[col][1] = max(xlimits[col][1], vals.max())
    return xlimits

def plot_all_cdfs(premium_df, standard_df, region, columns, source_groups, output_dir, xlimits):
    fig, axs = plt.subplots(len(source_groups), len(columns), figsize=(18, 12), sharey=True)
    for i, source in enumerate(source_groups):
        for j, column in enumerate(columns):
            ax = axs[i, j]
            for df, label in [(standard_df, "Standard"), (premium_df, "Premium")]:
                values = df[df["Source Group"] == source][column]
                values = pd.to_numeric(values, errors='coerce').dropna()
                if column == "RTT Ratio (Google/Non-Google)":
                    values = values[values <= 3]
                if len(values) == 0:
                    continue
                values = np.sort(values)
                cdf = np.arange(1, len(values)+1) / len(values)
                ax.step(values, cdf, label=label)
            ax.set_title(f"{column} - {source}", fontsize=9)
            ax.set_xlim(xlimits[column])
            if i == len(source_groups) - 1:
                ax.set_xlabel(column, fontsize=8)
            if j == 0:
                ax.set_ylabel("CDF", fontsize=8)
            ax.tick_params(axis='both', which='major', labelsize=7)
            ax.grid(True, linestyle='--', linewidth=0.4)
            if i == 0 and j == len(columns) - 1:
                ax.legend(fontsize=6, loc='lower right')

    fig.suptitle(f"CDFs for Region: {region}", fontsize=14)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, f"{region}_combined_cdfs.pdf"), format='pdf')
    plt.close(fig)

def main():
    std_dir = os.path.expanduser("~/reu/tofu-deployment-standard/google_exit_analysis")
    prem_dir = os.path.expanduser("~/reu/tofu-deployment-premium/google_exit_analysis")
    output_dir = os.path.expanduser("~/reu/figures/overlay_cdfs")

    columns = [
        "Median RTT to Last Google Node (ms)",
        "RTT Ratio (Google/Non-Google)",
        "Distance to Last Google Node (km)",
        "Hops Before Exit"
    ]
    source_groups = ['tranco-top1k', 'tranco-rank10k', 'tranco-rank100k', 'vultr*']

    std_files = {extract_region(f): os.path.join(std_dir, f) for f in os.listdir(std_dir) if f.endswith(".csv")}
    prem_files = {extract_region(f): os.path.join(prem_dir, f) for f in os.listdir(prem_dir) if f.endswith(".csv")}
    common_regions = sorted(set(std_files) & set(prem_files))

    xlimits = compute_global_limits(std_files, prem_files, columns, source_groups)

    for region in common_regions:
        print(f"Creating CDF panel for region: {region}")
        std_df = normalize_sources(pd.read_csv(std_files[region]))
        prem_df = normalize_sources(pd.read_csv(prem_files[region]))
        plot_all_cdfs(prem_df, std_df, region, columns, source_groups, output_dir, xlimits)

if __name__ == "__main__":
    main()

