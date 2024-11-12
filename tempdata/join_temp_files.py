import pandas as pd
import csv
import glob

temp_files = glob.glob('tempdata/temp_songs_*')

df_combined = pd.read_csv('tempdata/temp_songs.csv')
print("Joining tempdata/temp_songs.csv")

for infile in temp_files:
    df_combined = pd.concat([df_combined, pd.read_csv(infile)], ignore_index=True)
    print(f'Joining {infile}')

df_combined = df_combined[df_combined['Songs'] != 'set()']
df_combined = df_combined.drop_duplicates(subset='ID', keep='first')

df_combined.to_csv('tempdata/all_songs.csv',index=False)
print("All temp data joined to tempdata/all_songs.csv")