# Callahan_Database
Making a database of Callahan Videos

FILES:
use_api.py <playlist_id>
    Uses Youtube API to produce file "raw_data.csv". Includes video ID and all data apart from Songs

    playlist_id options: 
        paste playlist id: uses the given playlist
        --all: uses all known video playlists
        --nec: uses four playlists necessary to fill all years

use_selenium.py <playlist_id>
    Uses Selenium to produce "temp_songs.csv". Includes only video ID and Songs

utils.py <functions>

    Requires: raw_data.csv and temp_songs.csv
    NOTE: Add columns 'ID' and 'Songs' to header of temp_songs.csv

    if(fun == '--all'):
        extract_data()
        join_tables()
        description_search()
        rm_duplicates()
    elif(fun == '-e'):
        extract_data()
    elif(fun == '-j'):
        join_tables()
    elif(fun == '-d'):
        description_search()
    elif(fun == '-r'):
        rm_duplicates()

