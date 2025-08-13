import os
import pandas as pd

input_dir = os.path.expanduser("~/reu/tofu-deployment-premium/cleaned_traceroutes")
output_dir = os.path.expanduser("~/reu/tofu-deployment-premium/trimmed_traceroutes")
os.makedirs(output_dir, exist_ok=True)

def downsample_tranco_domains(df, max_domains=750):
    tranco_sources = ['tranco-top1k', 'tranco-rank10k', 'tranco-rank100k']
    df.columns = df.columns.str.strip()
    df['Source'] = df['Source'].astype(str).str.strip().str.lower()
    df['Destination'] = df['Destination'].astype(str).str.strip()

    final_frames = []

    for source in tranco_sources:
        group = df[df['Source'] == source]
        selected_domains = (
            group['Destination']
            .drop_duplicates()
            .sample(n=min(max_domains, group['Destination'].nunique()), random_state=42)
        )
        trimmed = group[group['Destination'].isin(selected_domains)]
        final_frames.append(trimmed)

    untouched = df[~df['Source'].isin(tranco_sources)]
    final_frames.append(untouched)

    return pd.concat(final_frames, ignore_index=True)


# Process all CSVs
for filename in os.listdir(input_dir):
    if filename.endswith(".csv"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.replace(".csv", "_trimmed.csv"))

        df = pd.read_csv(input_path)
        trimmed_df = downsample_tranco_domains(df)
        trimmed_df.to_csv(output_path, index=False)
        print(f"Trimmed and saved: {output_path}")

