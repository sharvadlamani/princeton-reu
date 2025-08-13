import os
import pandas as pd

input_dir = os.path.expanduser("~/reu/tofu-deployment-standard/downloads")
output_dir = os.path.expanduser("~/reu/tofu-deployment-standard/cleaned_traceroutes")
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.endswith(".csv"):
        filepath = os.path.join(input_dir, filename)
        df = pd.read_csv(filepath)

        # Normalize column names
        df.columns = df.columns.str.strip()

        # Strip and normalize Destination IP values
        df['Destination IP'] = df['Destination IP'].astype(str).str.strip().str.lower()

        # Match any variant of 'n/a'
        bad_domains = df[df["Destination IP"].isin(["n/a", "na", "nan"])]['Destination'].unique()

        print(f"{filename}: Removing {len(bad_domains)} unresolvable domains")

        # Drop all rows with those domains
        cleaned_df = df[~df["Destination"].isin(bad_domains)]

        output_path = os.path.join(output_dir, filename)
        cleaned_df.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")

