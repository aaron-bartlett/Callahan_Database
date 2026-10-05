import csv
import os
import sys

import yt_dlp

from utils import COOKIES_PATH, read_playlists, tempdata

songs_path = tempdata('temp_songs.csv')


def load_scraped_ids():
    # Write the header once if the file doesn't exist yet, and return any IDs
    # already scraped so re-runs/resumes don't hit the same video twice.
    ids_set = set()
    if not os.path.exists(songs_path) or os.path.getsize(songs_path) == 0:
        with open(songs_path, 'w', newline='', encoding='utf-8') as songsfile:
            csv.writer(songsfile).writerow(["ID", "Songs"])
    else:
        with open(songs_path, 'r', newline='', encoding='utf-8') as songsfile:
            reader = csv.reader(songsfile)
            next(reader, None)  # skip header
            for row in reader:
                if row:
                    ids_set.add(row[0])
    return ids_set


def get_playlist_video_ids(playlist_id):
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': COOKIES_PATH,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    return [entry['id'] for entry in info.get('entries', []) if entry and entry.get('id')]


def get_music_cards(video_id):
    # Returns a list of "Track - Artist" strings for every YouTube Music
    # card attached to the video.
    #
    # yt-dlp's built-in 'track'/'artist' fields read the old watch-page
    # layout (a metadataRowContainer next to the title) which YouTube has
    # since replaced with a "Music" card carousel inside the structured
    # description engagement panel. yt-dlp doesn't parse that new layout,
    # so we pull it out of the raw initial page data ourselves instead of
    # going through extract_info().
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': COOKIES_PATH,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ie = ydl.get_info_extractor('Youtube')
        ie.set_downloader(ydl)
        webpage = ie._download_webpage(video_url, video_id)
        initial_data = ie.extract_yt_initial_data(video_id, webpage) or {}

    cards = []
    for panel in initial_data.get('engagementPanels', []):
        section = panel.get('engagementPanelSectionListRenderer', {})
        if section.get('panelIdentifier') != 'engagement-panel-structured-description':
            continue
        items = section.get('content', {}).get('structuredDescriptionContentRenderer', {}).get('items', [])
        for item in items:
            card_list = item.get('horizontalCardListRenderer')
            if not card_list:
                continue
            header_title = card_list.get('header', {}).get('richListHeaderRenderer', {}).get('title', {}).get('simpleText')
            if header_title != 'Music':
                continue
            for card in card_list.get('cards', []):
                attrs = card.get('videoAttributeViewModel', {})
                track = attrs.get('title')
                artist = attrs.get('subtitle')
                if track:
                    cards.append(f"{track} - {artist}" if artist else track)
    return cards


if len(sys.argv) == 1:
    playlists = [input('Paste Playlist ID: ')]
elif sys.argv[1] == '--all':
    playlists = read_playlists()
else:
    playlists = [sys.argv[1]]

ids_set = load_scraped_ids()

with open(songs_path, 'a', newline='', encoding='utf-8') as songsfile:
    songs_writer = csv.writer(songsfile)

    for i, playlist_id in enumerate(playlists, 1):
        print(f"[{i}/{len(playlists)}] Playlist {playlist_id}")

        try:
            video_ids = get_playlist_video_ids(playlist_id)
        except Exception as e:
            print(f"  Skipping playlist {playlist_id}: {e}")
            continue

        print(f"  Found {len(video_ids)} videos in playlist {playlist_id}")
        for video_id in video_ids:
            if video_id in ids_set:
                continue
            ids_set.add(video_id)

            try:
                cards = get_music_cards(video_id)
                songs = "|".join(cards) if cards else "No Songs Detected"
            except Exception as e:
                print(f"ID: {video_id} | Error fetching metadata: {e}")
                songs = "No Songs Detected"

            print(f"ID: {video_id} | Songs: {songs}")
            songs_writer.writerow([video_id, songs])
            songsfile.flush()  # persist progress as we go, in case a later playlist/video fails

print(f"Song data written to {songs_path}")
