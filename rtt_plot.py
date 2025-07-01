import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV
df = pd.read_csv('google_exit_summary.csv')

# Filter only rows that exited Google
exited_df = df[df['Status'] == 'Exited Google']

# Convert RTT column to numeric (in case of stray text)
exited_df['Median RTT to Last Google Hop (ms)'] = pd.to_numeric(
    exited_df['Median RTT to Last Google Hop (ms)'], errors='coerce'
)

# Define RTT buckets
bins = [0, 10, 50, 100, 200, float('inf')]
labels = ['0-10ms', '10-50ms', '50-100ms', '100-200ms', '200ms+']
exited_df['RTT Range'] = pd.cut(
    exited_df['Median RTT to Last Google Hop (ms)'],
    bins=bins, labels=labels, right=False
)

# Count how many fall into each bucket
bucket_counts = exited_df['RTT Range'].value_counts().sort_index()

# Plot histogram
plt.figure(figsize=(10, 6))
bucket_counts.plot(kind='bar', color='orange')
plt.title('Histogram of Median RTT to Last Google Hop (Exited Google only)')
plt.xlabel('RTT Range')
plt.ylabel('Number of Destinations')
plt.grid(axis='y')
plt.tight_layout()

# Save to file
plt.savefig('rtt_histogram.png', dpi=300)

# Optional: display it too
plt.show()

