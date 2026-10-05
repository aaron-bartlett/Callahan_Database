import os
import shutil
import sys
import csv
import string
import pandas as pd

# All paths are anchored to this file's location so the scripts work no matter
# which directory they're run from. scripts/ holds the code and intermediate
# tempdata/; the final spreadsheet goes to output/ at the repo root, with a
# copy at the repo root itself for easy downloading.
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)
TEMPDATA_DIR = os.path.join(SCRIPTS_DIR, 'tempdata')
OUTPUT_DIR = os.path.join(REPO_ROOT, 'output')
PLAYLISTS_PATH = os.path.join(SCRIPTS_DIR, 'ultiworld_playlists.txt')
COOKIES_PATH = os.path.join(REPO_ROOT, 'cookies.txt')
FINAL_CSV_NAME = 'Callahan_Videos_2026.csv'
FINAL_CSV = os.path.join(OUTPUT_DIR, FINAL_CSV_NAME)
ROOT_CSV = os.path.join(REPO_ROOT, FINAL_CSV_NAME)

def tempdata(name):
    return os.path.join(TEMPDATA_DIR, name)

substrings_to_filter = ["Callahan", "for", "For", "|", ":", "Nominee", "Donovan", "Award"]
all_years = ["2026", "2025", "2024", "2023", "2022", "2021", "2020",
             "2019", "2018", "2017", "2016", "2015",
             "2014", "2013", "2012"]

def read_playlists(path=PLAYLISTS_PATH):
    # One playlist ID per line. Blank lines and '#' comments (whole-line or
    # trailing) are ignored, so playlists can be disabled by commenting them out.
    playlists = []
    with open(path, 'r') as f:
        for line in f:
            playlist_id = line.split('#', 1)[0].strip()
            if playlist_id:
                playlists.append(playlist_id)
    return playlists

def extract_songs(description):
    # Find the index of the substring "song"
    index_song = description.lower().find("song")
    index_music = description.lower().find("music")
    
    # If "song" is found, slice the string from that index onwards
    if index_song != -1:
        return (description[index_song:], 1)
    elif index_music != -1:
        return (description[index_music:], 1)
    else:
        return ("no songs found", 0)


def extract_data(infile=tempdata('raw_data.csv'), outfile=tempdata('videos_data.csv')):

    with open(infile, 'r', newline='') as raw_data:
        raw_reader = csv.reader(raw_data)

        with open(outfile, 'w+', newline='') as fullfile:
            data_writer = csv.writer(fullfile)
            data_writer.writerow(["ID","URL","Title","Name","Year","Div","Views"])



            # Dev for "song" and "music" frequency in descriptions
            song_tot = 0
            none_tot = 0

            # skip header row
            next(raw_reader)

            ids_set = set()

            for row in raw_reader:
                video_id, title, description, view_count = row

                if video_id not in ids_set:

                    ids_set.add(video_id)

                    # URL from video_id
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    # Nominee Name from Title
                    nominee_name = title

                    for substr in substrings_to_filter:
                        nominee_name = nominee_name.replace(substr, "")            

                    # Video Year
                    video_year = "unknown"
                    for year in all_years:
                        if year in title:
                            video_year = year
                            nominee_name = nominee_name.replace(year, "")

                    # D1 Callahan or D3 Donovan
                    d1_d3 = "D1"
                    if "Donovan" in title:
                        d1_d3 = "D3"

                    songs, flag = extract_songs(description)
                    if(flag == 1):
                        song_tot += 1
                    elif(flag == 0):
                        none_tot += 1

                    #data_writer.writerow([index, video_id, video_url, title, nominee_name, video_year, d1_d3, view_count, songs])
                    data_writer.writerow([video_id, video_url, title, nominee_name, video_year, d1_d3, view_count])


            print(f"{song_tot} Videos with Songs in Description")
            print(f"{none_tot} Videos with no songs found")

def join_tables(infile1 = tempdata('videos_data.csv'),
                infile2 = tempdata('temp_songs.csv'),
                outfile = tempdata('merged_videos.csv')):
    # Read CSV files into pandas DataFrames
    df1 = pd.read_csv(infile1)
    df2 = pd.read_csv(infile2)

    #print(videos_df.columns)
    #videos_df.drop(columns=['Index'])

    # Perform a right join on the "videos" and "songs" DataFrames
    merged_df = pd.merge(df1, df2, on='ID', how='outer')

    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv(outfile, index=False)
    print(f"Merged tables to {outfile}")

MISSING_SONGS_VALUES = {'', 'set()', 'no songs found', 'no songs detected'}

def description_search(infile1=tempdata('raw_data.csv'),
                        infile2=tempdata('merged_videos.csv'),
                        outfile=FINAL_CSV):
    # Read the 'raw' CSV file
    with open(infile1, 'r') as raw_file:
        raw_reader = csv.DictReader(raw_file)
        raw_data = {row['ID']: row['Description'] for row in raw_reader}

    with open(infile2, 'r') as videos_file:
        videos_reader = csv.DictReader(videos_file)

        with open(outfile, 'w', newline='') as outf:

            out_writer = csv.DictWriter(outf, fieldnames=videos_reader.fieldnames)
            out_writer.writeheader()

            for row in videos_reader:
                songs_value = (row.get('Songs') or '').strip().lower()
                if songs_value in MISSING_SONGS_VALUES and row['ID'] in raw_data:
                    row['Songs'] = extract_songs(raw_data[row['ID']])[0]
                out_writer.writerow(row)
    print(f"Descriptions searched and saved to {outfile}")

def rm_duplicates(infile = FINAL_CSV):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(infile)
    # Identify rows where the 'ID' is the same as the previous row
    df_cleaned = df.drop_duplicates(subset=['ID'])
    # Save the cleaned DataFrame to a new CSV file
    df_cleaned.to_csv(infile, index=False)
    print(f"Processed data saved to {infile}")

def publish(infile=FINAL_CSV, outfile=ROOT_CSV):
    # Copy the final spreadsheet to the repo root, where the README's
    # download link points.
    shutil.copyfile(infile, outfile)
    print(f"Copied {infile} to {outfile}")

def merge_drop_duplicates(infile1, infile2, outfile):

    df1 = pd.read_csv(infile1)
    df2 = pd.read_csv(infile2)
    df_combined = pd.concat([df1, df2], ignore_index=True)

    df_combined.drop_duplicates(subset='ID', keep='first').to_csv(outfile, index=False)
    print(f"Processed data saved to {outfile}")
    

def add_non_duplicates(input_file, output_file):
    # Read existing data from out.csv
    existing_rows = set()
    # Read data from input CSV file and append non-duplicate rows to out.csv
    with open(input_file, 'r', newline='') as infile:
        with open(output_file, 'a', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            for row in reader:
                if tuple(row) not in existing_rows:
                    writer.writerow(row)
                    existing_rows.add(tuple(row))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        fun = input('Function to run (--all: run all, -e: extract_data, -j: join_tables, '
                     '-d: description_search, -r: rm_duplicates, -p: publish, -m: merge into output): ')
    else:
        fun = sys.argv[1]

    if(fun == '--all'):
        extract_data()
        join_tables()
        description_search()
        rm_duplicates()
        publish()
    elif(fun == '-e'):
        extract_data()
    elif(fun == '-j'):
        join_tables()
    elif(fun == '-d'):
        if(len(sys.argv) == 3):
            description_search(outfile=sys.argv[2])
        else:
            description_search()
    elif(fun == '-r'):
        if(len(sys.argv) == 3):
            rm_duplicates(sys.argv[2])
        else:
            rm_duplicates()
    elif(fun == '-p'):
        publish()
    elif(fun == '-m'):
        if(len(sys.argv) == 2):
            file = input(f"Which file to merge with {FINAL_CSV}? ")
            join_tables(file, FINAL_CSV, FINAL_CSV)
        elif(len(sys.argv) == 5):
            join_tables(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print("Usage: python utils.py -m infile1 infile2 outfile")