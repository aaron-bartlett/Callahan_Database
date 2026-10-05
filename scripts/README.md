# Callahan_Database — scripts

> This is the pipeline documentation. For an overview of the data itself and a
> download link, see the [top-level README](../README.md).

All scripts live in this `scripts/` folder. Paths inside them are anchored to
the script's own location, so they can be run from anywhere (e.g.
`python scripts/use_api.py --all` from the repo root, or `python use_api.py
--all` from inside `scripts/`). Intermediate files go to `scripts/tempdata/`;
the final spreadsheet goes to `output/` at the repo root and is copied to the
repo root itself.

Builds a spreadsheet of Callahan/Donovan nomination videos: pulls video metadata
from the YouTube Data API, scrapes each video's "Music in this video" song
credits with Selenium, then joins everything into one CSV.

Previous versions of every script here are saved in [`ARCHIVE/`](ARCHIVE/) —
untouched copies from before the July 2026 fixes described below, kept for
reference/rollback.

## Pipeline overview

```
use_api.py       -->  tempdata/raw_data.csv
use_selenium.py  -->  tempdata/temp_songs.csv
utils.py -e      -->  tempdata/videos_data.csv   (from raw_data.csv)
utils.py -j      -->  tempdata/merged_videos.csv (videos_data.csv + temp_songs.csv)
utils.py -d      -->  ../output/Callahan_Videos_2026.csv   <-- final spreadsheet
utils.py -r      -->  (de-dupes the final spreadsheet in place)
utils.py -p      -->  ../Callahan_Videos_2026.csv          (copy for downloading)
```

(`tempdata/` paths above are relative to `scripts/`.)

Run `use_api.py` and `use_selenium.py` first (in either order — they write to
different files), then run the `utils.py` steps in order (or `utils.py --all`
to run the last five in one shot).

## Setup

- Conda env: `conda activate apis` (has `selenium`, `google-api-python-client`,
  `pandas` installed).
- Chrome + a matching `chromedriver` on PATH or in `chromedriver-mac-arm64/`
  (at the repo root, gitignored).
- For `use_ytdlp.py`: a YouTube `cookies.txt` at the repo root (gitignored).
- For `create_spotify_playlist.py`: Spotify API credentials in `.env` at the
  repo root (gitignored).
- A YouTube Data API v3 key, exported as an environment variable:
  ```
  export YOUTUBE_API_KEY='your-key-here'
  ```
  **Do not hardcode the key in `use_api.py`.** It used to be hardcoded and a
  real key ended up committed to the working tree — see "Security note" below.

## Files

### Active pipeline

- **`use_api.py`** — Calls the YouTube API to pull, for each video in one or
  more playlists: ID, title, description, view count. Appends rows to
  `tempdata/raw_data.csv` (writes the header once, on first run).
  ```
  python use_api.py <playlist_id>   # one playlist
  python use_api.py --all           # every playlist in ultiworld_playlists.txt
  python use_api.py --new           # just the "new_playlists" subset
  python use_api.py --two           # just the "two_playlits" subset
  python use_api.py                 # prompts for a playlist ID
  ```
  Requires `YOUTUBE_API_KEY` to be set. Skips (and logs) any video whose API
  call fails, instead of writing bad data for it.

- **`use_selenium.py`** — Opens a playlist in headless Chrome, scrolls to load
  every video, then visits each video page and scrapes the "Music in this
  video" attribution block. Appends rows (`ID, Songs`, pipe-separated if
  multiple) to `tempdata/temp_songs.csv` (writes the header once, on first
  run, and skips IDs already present in the file so reruns don't re-scrape).
  ```
  python use_selenium.py <playlist_id>
  python use_selenium.py --all      # every playlist in ultiworld_playlists.txt, one after another
  python use_selenium.py            # prompts for a playlist ID
  ```
  With `--all`, it reuses one browser session and runs every playlist in
  `ultiworld_playlists.txt` back to back, saving each video's row to
  `tempdata/temp_songs.csv` as it goes (not just at the end), and skips a
  playlist (logging why) rather than aborting the whole run if that playlist
  fails to load.

- **`use_ytdlp.py`** — Alternative to `use_selenium.py` for the same job (fill
  in `tempdata/temp_songs.csv`), using [yt-dlp](https://github.com/yt-dlp/yt-dlp)
  instead of a headless browser. For each playlist it asks yt-dlp for the list
  of video IDs directly (no scrolling/DOM scraping needed), then for each video
  reads the YouTube Music card metadata (track/artist, and multi-track
  compilations if present) straight from yt-dlp's extracted info. Writes rows
  as `Track - Artist` (pipe-separated if a video has multiple cards), same
  header/resume/`--all` behavior as `use_selenium.py`.
  ```
  pip install yt-dlp   # not yet in the `apis` conda env — install once

  python use_ytdlp.py <playlist_id>
  python use_ytdlp.py --all      # every playlist in ultiworld_playlists.txt
  python use_ytdlp.py            # prompts for a playlist ID
  ```
  Since it doesn't drive a real browser, it's faster and less likely to break
  when YouTube tweaks its page markup than `use_selenium.py` is — but it
  depends on yt-dlp's YouTube extractor staying up to date instead. Use
  whichever one is working better at the time; both write to the same
  `tempdata/temp_songs.csv`, so don't run both back-to-back expecting to merge
  their output — pick one per pipeline run (or manually reconcile if you want
  to compare their results).

- **`ultiworld_playlists.txt`** — The shared list of playlist IDs used by
  `use_api.py --all`, `use_selenium.py --all`, and `use_ytdlp.py --all`, one ID
  per line. `#` starts
  a comment — either a trailing note (`PLxxxx # Ultiworld 2024`) or, with the
  `#` at the start of the line, a disabled/retired playlist that's kept for
  reference but won't be scraped. Add a new playlist by adding a line; retire
  one by prefixing it with `#`.

- **`utils.py`** — Post-processing steps, run as `python utils.py <flag>`:
  - `-e` — `extract_data()`: reads `tempdata/raw_data.csv`, derives nominee
    name / year / division (D1 Callahan vs. D3 Donovan) from the title, dedupes
    by ID, writes `tempdata/videos_data.csv`.
  - `-j` — `join_tables()`: outer-joins `tempdata/videos_data.csv` with
    `tempdata/temp_songs.csv` on `ID`, writes `tempdata/merged_videos.csv`.
  - `-d` — `description_search()`: for any row still missing songs, falls back
    to regex-searching the video description for a "song"/"music" mention.
    Writes the final spreadsheet to `output/Callahan_Videos_2026.csv` at the
    repo root (pass a different path as a second argument to use a different
    output filename).
  - `-r [file]` — `rm_duplicates()`: drops duplicate IDs from the final
    spreadsheet in place (defaults to `output/Callahan_Videos_2026.csv`).
  - `-p` — `publish()`: copies `output/Callahan_Videos_2026.csv` to
    `Callahan_Videos_2026.csv` at the repo root, which is what the top-level
    README's download link points to.
  - `-m infile1 infile2 outfile` — `join_tables()` with explicit paths, for
    manually merging an extra data file into an existing spreadsheet. Run with
    no extra args (`-m` alone) to merge a file you'll be prompted for into
    `output/Callahan_Videos_2026.csv` in place.
  - `--all` — runs `-e`, `-j`, `-d`, `-r`, `-p` in sequence.
  - The output filename is set once in `FINAL_CSV_NAME` near the top of
    `utils.py`; change it there for a new year.
  - Run with no arguments to get an interactive prompt for which step to run.

- **`create_spotify_playlist.py`** — Reads the final spreadsheet and builds a
  Spotify playlist from the song credits of videos above a view threshold.
  ```
  python create_spotify_playlist.py                     # views > 5000
  python create_spotify_playlist.py --min-views 10000
  python create_spotify_playlist.py --mode year         # 2026 needs >3000, +1000 per year back
  python create_spotify_playlist.py --playlist-name "..." --public
  ```
  Requires `spotipy` and `python-dotenv`, plus Spotify credentials
  (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`) in the
  root `.env`.

- **`analysis.py`** — Standalone (local only, gitignored): loads
  `output/Callahan_Videos.csv` and
  prints the 5 most-viewed videos. Not part of the join pipeline; point it at
  a different file by editing the hardcoded path if you want to inspect a
  different spreadsheet.

### Legacy / reference (not part of the active flow, local only / gitignored)

- **`use_api_redacted.py`** / **`use_selenium_redacted.py`** — Earlier,
  git-safe copies of the two scripts above (API key placeholder, older
  playlist logic, older/broken Selenium scraping approach). Now that
  `use_api.py` reads its key from an environment variable instead of hardcoding
  it, these are superseded — keeping them around is optional and they will
  drift out of sync with the real scripts if not maintained. Safe to delete
  once you're comfortable relying on the `YOUTUBE_API_KEY` env var approach.
- **`tempdata/join_temp_files.py`** — One-off helper that concatenates all the
  historical `tempdata/temp_songs_*.csv` fragments (from older scraping runs)
  into `tempdata/all_songs.csv`. Not part of the current pipeline; only
  relevant if you're reconciling old data.

## Security note

`use_api.py` now reads its key from the `YOUTUBE_API_KEY` environment variable
and contains no secrets, so it is tracked normally (the old `.gitignore` rule
for it was removed). However, **earlier commits in this repo's history contain
a real, hardcoded API key.** Rewriting history won't un-expose it if the repo
has ever been public — rotate (delete and recreate) that key in the Google
Cloud console.

Other secrets — `.env` (Spotify credentials), `.cache` (Spotify OAuth token),
`cookies.txt` (YouTube session cookies) — live at the repo root and are
gitignored. Never commit them.

## What changed in this fix (see `ARCHIVE/` for the "before")

- `use_api.py`: API key now comes from `YOUTUBE_API_KEY` (was hardcoded);
  writes a proper CSV header on first run (was missing, which caused
  `utils.py -e` to silently skip the first video); no longer writes
  stale/wrong data for a video when its API call fails (was reusing the
  previous video's response).
- `use_selenium.py`: writes a proper `ID,Songs` header on first run (was
  missing entirely — previously had to be added by hand, and without it
  `utils.py -j` would corrupt the merge by treating the first data row as a
  header); now skips IDs already scraped in a prior run instead of only
  within the current run.
- `utils.py`: `description_search()`'s check for "no songs yet" was matching a
  string format (`'set()'`) the current scraper no longer produces, so the
  description fallback was silently never triggering — fixed to match the
  actual sentinel values; `-m` with no extra args was merging into a
  throwaway temp file instead of updating the output spreadsheet — fixed;
  removed a leftover debug `print()` that dumped every matched description to
  the console.
- Added `ultiworld_playlists.txt` as the single shared source of playlist IDs
  (previously the full list only lived hardcoded inside `use_api.py`) and a
  `read_playlists()` helper in `utils.py` that both scripts use to read it.
  `use_selenium.py` gained a `--all` flag that loops over every playlist in
  that file in one run instead of requiring a separate manual invocation per
  playlist.
