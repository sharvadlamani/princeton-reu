import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from glob import glob

# Style setup
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.family'] = 'serif'
plt.style.use('tableau-colorblind10')

# Directories
directories = {
    'standard': os.path.expanduser("~/reu/tofu-deployment-standard/google_exit_analysis"),
    'premium': os.path.expanduser("~/reu/tofu-deployment-premium/google_exit_analysis")
}
output_dir = os.path.expanduser("~/reu/google_exit_cdfs_top35_per_rank")
os.makedirs(output_dir, exist_ok=True)

# Use the actual path from upload
tranco_path = "top-1m.csv"
tranco = pd.read_csv(tranco_path, header=None, names=["rank", "domain"])
tranco["domain"] = tranco["domain"].str.lower()

# Updated rank cutoffs
rank_groups = {
    'tranco-top1k': set(tranco.iloc[0:1000]["domain"]),
    'tranco-rank10k': set(tranco.iloc[10000:12000]["domain"]),
    'tranco-rank100k': set(tranco.iloc[100000:]["domain"])
}

# Metrics
metrics = {
    'Median RTT to Last Google Node (ms)': {'xlabel': 'Median RTT (ms)', 'max': None},
    'RTT Ratio (Google/Non-Google)': {'xlabel': 'RTT Ratio', 'max': 3},
    'Distance to Last Google Node (km)': {'xlabel': 'Distance (km)', 'max': None},
    'Hops Before Exit': {'xlabel': 'Hops Before Exit', 'max': None},
}

# Main loop
for label, dir_path in directories.items():
    for filepath in glob(os.path.join(dir_path, "*.csv")):
        df = pd.read_csv(filepath)
        df['Destination'] = df['Destination'].str.lower()
        df_domains = set(df['Destination'].unique())

        # Grab highest-ranked intersecting domains per group
        intersect_domains = {}
        for group, domain_set in rank_groups.items():
            ranked = [d for d in tranco["domain"] if d in domain_set and d in df_domains]
            intersect_domains[group] = ranked[:35]

        # Warn if groups are too small
        for group, domains in intersect_domains.items():
            if len(domains) < 5:
                print(f"⚠️  Warning: Only {len(domains)} domains matched for {group} in {filepath}")

        # Tag rows by source group
        def assign_group(row):
            dest = row['Destination']
            source = row['Source']
            if isinstance(source, str) and 'vultr' in source.lower():
                return 'vultr*'
            for group, domains in intersect_domains.items():
                if dest in domains:
                    return group
            return 'other'

        df['Source Group'] = df.apply(assign_group, axis=1)
        filtered_df = df[df['Source Group'].isin(['tranco-top1k', 'tranco-rank10k', 'tranco-rank100k', 'vultr*'])]

        base = os.path.basename(filepath).replace(".csv", "")
        for metric, settings in metrics.items():
            fig, ax = plt.subplots(figsize=(10, 6))
            for group in ['tranco-top1k', 'tranco-rank10k', 'tranco-rank100k', 'vultr*']:
                vals = pd.to_numeric(filtered_df[filtered_df['Source Group'] == group][metric], errors='coerce').dropna()
                if settings['max'] is not None:
                    vals = vals[vals <= settings['max']]
                if len(vals) == 0:
                    continue
                sorted_vals = np.sort(vals)
                cdf_vals = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
                ax.plot(sorted_vals, cdf_vals, label=group)

            ax.set_title(f"{metric} - {base} ({label})")
            ax.set_xlabel(settings['xlabel'])
            ax.set_ylabel("CDF")
            ax.legend()
            fname = f"{base}_{metric.replace(' ', '_').replace('/', '_')}_top35_cdf.pdf"
            fig.savefig(os.path.join(output_dir, fname), bbox_inches='tight')
            plt.close(fig)

