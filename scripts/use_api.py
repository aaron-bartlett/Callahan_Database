from googleapiclient.discovery import build
import csv
import os
import sys

from utils import read_playlists, tempdata

API_KEY = os.environ.get('YOUTUBE_API_KEY')
if not API_KEY:
    sys.exit(
        "Error: YOUTUBE_API_KEY environment variable is not set.\n"
        "Run: export YOUTUBE_API_KEY='your-api-key-here'"
    )

# Path to raw data
raw_path = tempdata('raw_data.csv')

# Full playlist list lives in ultiworld_playlists.txt (one ID per line,
# '#' comments/lines ignored) so it's shared with use_selenium.py.
all_playlists = read_playlists()

new_playlists = [
    'PLvgVvH9p4IEETb53S07BUcpoHKELKRMEq', # Ultiworld 2025
    'PLvgVvH9p4IEHNOPscRMRK2FhMDLLJGbZC', # Ultiworld 2024
    'PLvgVvH9p4IEEgpA3-TDsT6scPZghsz3JQ', # Ultiworld 2021
    'PLvgVvH9p4IEHGS0MIrA61oCkuYCSkeRpH', # Ultiworld 2020
    'PLtY3QCjnzOF8zxb66uJWYXCKLS2xdsRa6', # GOAT PLAYLIST
] 

two_playlits = ['PLvgVvH9p4IEEgpA3-TDsT6scPZghsz3JQ', # Ultiworld 2021
             'PLvgVvH9p4IEHGS0MIrA61oCkuYCSkeRpH'] # Ultiworld 2020

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

playlists = []
if len(sys.argv) == 1:
    playlists.append(input('Paste Playlist ID: '))
elif (sys.argv[1] == '--all'):
    playlists = all_playlists
elif (sys.argv[1] == '--new'):
    playlists = new_playlists
elif(sys.argv[1] == '--two'):
    playlists = two_playlits
elif (sys.argv[1] == '-h'):
    print("HELP")
    exit(1)
else:
    playlists.append(sys.argv[1])

# Write the header once if raw_path doesn't exist yet, since every write below
# uses append mode (rows accumulate across multiple playlists/runs).
if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
    with open(raw_path, 'w', newline='') as rawfile:
        csv.writer(rawfile).writerow(["ID", "Title", "Description", "Views"])

for playlist_id in playlists:

    # List of Videos in Playlist
    playlist_items_request = youtube.playlistItems().list(
        part='snippet,status,contentDetails',
        playlistId=playlist_id,
        maxResults=50 
    )

    playlist_items_response = playlist_items_request.execute()

    with open(raw_path, 'a', newline='') as rawfile:

        raw_writer = csv.writer(rawfile)

        # For Video in Playlist
        for item in playlist_items_response['items']:

            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            #video_duration = item['contentDetails']['duration']
            #video_description = item['snippet']['description']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            privacy = item['status']['privacyStatus']
            #print(privacy)
            if(privacy != 'public'):
                continue
            # Details and Description of Video
            video_request = youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            )
            
            try:
                video_response = video_request.execute()
            except Exception as e:
                print(f"Skipping {video_id}: {e}")
                continue

            video_description = video_response['items'][0]['snippet']['description']
            view_count = video_response['items'][0]['statistics']['viewCount']


            # Print video details
            #print(f"Title: {video_title}")
            #print(f"Description: {video_description}")
            #print(f"URL: {video_url} \n \n")
            print(video_title)

            raw_writer.writerow([video_id, video_title, video_description, view_count])

    while("nextPageToken" in playlist_items_response):
        playlist_items_request = youtube.playlistItems().list(
            part='snippet,status,contentDetails',
            playlistId=playlist_id,
            pageToken=playlist_items_response["nextPageToken"],
            maxResults=50
        )

        playlist_items_response = playlist_items_request.execute()

        with open(raw_path, 'a', newline='') as rawfile:

            raw_writer = csv.writer(rawfile)

            # For Video in Playlist
            for item in playlist_items_response['items']:

                video_id = item['snippet']['resourceId']['videoId']
                video_title = item['snippet']['title']
                #video_description = item['snippet']['description']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                privacy = item['status']['privacyStatus']
                #print(privacy)
                if(privacy != 'public'):
                    continue
                # Details and Description of Video
                video_request = youtube.videos().list(
                    part='snippet,statistics',
                    id=video_id
                )
                
                try:
                    video_response = video_request.execute()
                except Exception as e:
                    print(f"Skipping {video_id}: {e}")
                    continue

                video_description = video_response['items'][0]['snippet']['description']
                view_count = video_response['items'][0]['statistics']['viewCount']
                
                
                # Print video details
                #print(f"Title: {video_title}")
                #print(f"Description: {video_description}")
                #print(f"URL: {video_url} \n \n")
                print(video_title)

                #raw_writer.writerow([video_id, video_title, video_description, view_count, video_duration])
                raw_writer.writerow([video_id, video_title, video_description, view_count])

print(f"API Data written to {raw_path}")


        
