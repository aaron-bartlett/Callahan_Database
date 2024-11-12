from googleapiclient.discovery import build
import csv
import sys

API_KEY = '[REDACTED]'

all_playlists = ['PLvgVvH9p4IEHNOPscRMRK2FhMDLLJGbZC', # Ultiworld 2024
             'PLvgVvH9p4IEElJus8QqSjYlSXPk5pfbgL', # Ultiworld 2023
             'PLvgVvH9p4IEFdvSjDAZJOfVRNLWFdtwLj', # Ultiworld 2022
             'PLvgVvH9p4IEEgpA3-TDsT6scPZghsz3JQ', # Ultiworld 2021
             'PLvgVvH9p4IEHGS0MIrA61oCkuYCSkeRpH', # Ultiworld 2020
             'PLGifQDmxfUzYubuJc59hTUABd04nlAU5c', # Syracuse 2020
             'PLvgVvH9p4IEHE-soVbHGrNLJjdQvS_L5y', # Ultiworld 2010s
             'PLdw8cj3Xb9jhnLOi-xVcAaqByCMsr9ZCg', # Jonah's Best
             'PLXbGyDmmb1MEQD-vYLWWYKYZDUjNHDvaa', # No Name 2017
             'PLXbGyDmmb1MFYa11qYdGii7qxBdsHLS3y', # No Name 2015
             'PLFMFBmU783XV-RNsxk8MSVcOU5gD-6Ib2', # Jacob 2016
             'PL_OJnOESreRLIxaGAinCuU-FSFlN2nOxE', # Joe 2019
             'PLtY3QCjnzOF8zxb66uJWYXCKLS2xdsRa6'] # GOAT PLAYLIST


necessary_playlists = ['PLvgVvH9p4IEHNOPscRMRK2FhMDLLJGbZC', # Ultiworld 2024
                 'PLvgVvH9p4IEEgpA3-TDsT6scPZghsz3JQ', # Ultiworld 2021
             'PLvgVvH9p4IEHGS0MIrA61oCkuYCSkeRpH', # Ultiworld 2020
             'PLtY3QCjnzOF8zxb66uJWYXCKLS2xdsRa6'] # GOAT PLAYLIST

two_playlits = ['PLvgVvH9p4IEEgpA3-TDsT6scPZghsz3JQ', # Ultiworld 2021
             'PLvgVvH9p4IEHGS0MIrA61oCkuYCSkeRpH'] # Ultiworld 2020

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

playlists = []
if len(sys.argv) == 1:
    playlists.append(input('Paste Playlist ID: '))
elif (sys.argv[1] == '--all'):
    playlists = all_playlists
elif (sys.argv[1] == '--nec'):
    playlists = necessary_playlists
elif(sys.argv[1] == '--two'):
    playlists = two_playlits
elif (sys.argv[1] == '-h'):
    print("HELP")
    exit(1)
else:
    playlists.append(sys.argv[1])


for playlist_id in playlists:

    # List of Videos in Playlist
    playlist_items_request = youtube.playlistItems().list(
        part='snippet,status',
        playlistId=playlist_id,
        maxResults=50 
    )

    playlist_items_response = playlist_items_request.execute()

    with open('raw_data.csv', 'a', newline='') as rawfile:

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
                print(e)

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
            part='snippet,status',
            playlistId=playlist_id,
            pageToken=playlist_items_response["nextPageToken"],
            maxResults=50
        )

        playlist_items_response = playlist_items_request.execute()

        with open('raw_data.csv', 'a', newline='') as rawfile:

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
                    print(e)

                video_description = video_response['items'][0]['snippet']['description']
                view_count = video_response['items'][0]['statistics']['viewCount']
                
                
                # Print video details
                #print(f"Title: {video_title}")
                #print(f"Description: {video_description}")
                #print(f"URL: {video_url} \n \n")
                print(video_title)

                raw_writer.writerow([video_id, video_title, video_description, view_count])
            
            

        
