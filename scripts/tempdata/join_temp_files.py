import pandas as pd
import csv
import glob
import os

# Paths are relative to this file (scripts/tempdata/), not the working directory.
TEMPDATA_DIR = os.path.dirname(os.path.abspath(__file__))

temp_files = glob.glob(os.path.join(TEMPDATA_DIR, 'temp_songs_*'))

df_combined = pd.read_csv(os.path.join(TEMPDATA_DIR, 'temp_songs.csv'))
print("Joining tempdata/temp_songs.csv")

for infile in temp_files:
    df_combined = pd.concat([df_combined, pd.read_csv(infile)], ignore_index=True)
    print(f'Joining {infile}')

df_combined = df_combined[df_combined['Songs'] != 'set()']
df_combined = df_combined.drop_duplicates(subset='ID', keep='first')

df_combined.to_csv(os.path.join(TEMPDATA_DIR, 'all_songs.csv'),index=False)
print("All temp data joined to tempdata/all_songs.csv")