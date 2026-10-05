import argparse
import csv
import os
import sys

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from utils import FINAL_CSV, REPO_ROOT

load_dotenv(os.path.join(REPO_ROOT, ".env"))

videos_path = FINAL_CSV
SCOPE = "playlist-modify-public playlist-modify-private"


def year_threshold(year):
    # 2026 requires 3000 views; every year further back adds 1000.
    return 3000 + (2026 - year) * 1000


def parse_songs(songs_field):
    # Songs are stored as "Track - Artist" entries joined with "|"; split on
    # the last " - " since track titles can themselves contain " - ".
    if not songs_field or songs_field.strip().lower() in ("no songs detected", "no songs found"):
        return []
    songs = []
    for entry in songs_field.split("|"):
        entry = entry.strip()
        if not entry:
            continue
        track, sep, artist = entry.rpartition(" - ")
        songs.append((track, artist) if sep else (entry, None))
    return songs


def load_candidates(mode, min_views):
    candidates = []
    with open(videos_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            views = float(row["Views"]) if row["Views"] else 0

            if mode == "flat":
                if views <= min_views:
                    continue
            else:
                year = row["Year"]
                if not year.isdigit():
                    continue
                if views <= year_threshold(int(year)):
                    continue

            candidates.extend(parse_songs(row["Songs"]))
    return candidates


def find_track_uris(sp, candidates):
    seen = set()
    uris = []
    not_found = []
    for track, artist in candidates:
        key = (track.lower(), (artist or "").lower())
        if key in seen:
            continue
        seen.add(key)

        query = f"track:{track} artist:{artist}" if artist else f"track:{track}"
        if len(query) > 200:
            continue
        results = sp.search(q=query, type="track", limit=1)
        items = results["tracks"]["items"]
        if items:
            uris.append(items[0]["uri"])
        else:
            not_found.append(f"{track} - {artist}" if artist else track)
    return uris, not_found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["flat", "year"], default="flat",
        help="flat: Views > --min-views for every video. "
             "year: threshold scales by year (2026 needs >3000, +1000 per year back).",
    )
    parser.add_argument("--min-views", type=int, default=5000, help="Only used with --mode flat")
    parser.add_argument("--playlist-name", default=None)
    parser.add_argument("--public", default=False, action="store_true")
    args = parser.parse_args()

    playlist_name = args.playlist_name or (
        f"Callahan Songs (Views > {args.min_views})" if args.mode == "flat"
        else "Callahan Video Songs"
    )

    candidates = load_candidates(args.mode, args.min_views)
    print(f"Found {len(candidates)} song credits matching the view threshold.")
    if not candidates:
        sys.exit(0)

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
    user_id = sp.current_user()["id"]

    uris, not_found = find_track_uris(sp, candidates)
    print(f"Matched {len(uris)} tracks on Spotify; {len(not_found)} not found.")

    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=args.public)
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist["id"], uris[i:i + 100])

    print(f"Created playlist '{playlist_name}': {playlist['external_urls']['spotify']}")
    if not_found:
        print("\nNot found on Spotify:")
        for song in not_found:
            print(f"  - {song}")


if __name__ == "__main__":
    main()
