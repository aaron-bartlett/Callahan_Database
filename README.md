# Callahan Database

A spreadsheet of every Callahan (D1) and Donovan (D3) nomination video on
YouTube, with its view count and the songs used in the video.

**[⬇ Download Callahan_Videos_2026.csv](https://raw.githubusercontent.com/aaron-bartlett/Callahan_Database/main/Callahan_Videos_2026.csv)**
(if it opens as text in your browser, use *File → Save Page As…* or
right-click the link → *Save Link As…*)

## The data

`Callahan_Videos_2026.csv` has one row per video (1,082 videos in the current
version), built from the Ultiworld Callahan/Donovan YouTube playlists for
2010s–2026. Columns:

| Column  | Description |
|---------|-------------|
| `ID`    | YouTube video ID (unique per row). |
| `URL`   | Link to the video: `https://www.youtube.com/watch?v=<ID>`. |
| `Title` | Video title as it appears on YouTube. |
| `Name`  | Nominee name, derived by stripping words like "Callahan", "Donovan", "Nominee", "for", and the year from the title. May have extra whitespace or leftover punctuation. |
| `Year`  | Nomination year parsed from the title, or `unknown` if no year was found. |
| `Div`   | `D1` (Callahan) or `D3` (Donovan, i.e. the title contains "Donovan"). |
| `Views` | YouTube view count at the time the data was pulled. |
| `Songs` | Music used in the video (see below). |

The `Songs` column takes one of three forms:

1. **`Track - Artist`** — taken from YouTube's "Music in this video" credits.
   Videos with several credited songs list them separated by `|`, e.g.
   `Song A - Artist A|Song B - Artist B`.
2. **Description excerpt** — when YouTube has no music credit, the text of the
   video description from the first mention of "song" or "music" onward.
   This is unstructured text and may need manual cleanup.
3. **`No Songs Detected`** (or empty) — neither source turned up a song.

The same file is also kept at
[`output/Callahan_Videos_2026.csv`](output/Callahan_Videos_2026.csv), which is
where the pipeline writes it.

## How it's built

```
YouTube playlists (scripts/ultiworld_playlists.txt)
        │
        ├── use_api.py ─────────────► video ID, title, description, views
        │     (YouTube Data API)
        │
        └── use_ytdlp.py / use_selenium.py ─► "Music in this video" credits
              (yt-dlp or headless Chrome)
        │
        ▼
utils.py --all
   1. extract   – parse nominee name / year / division from titles, de-dupe
   2. join      – merge video metadata with song credits on video ID
   3. describe  – fill missing songs from the video description
   4. de-dupe   – drop any duplicate IDs
   5. publish   – copy output/Callahan_Videos_2026.csv to the repo root
```

1. **Collect metadata.** `use_api.py` lists every public video in each playlist
   and records its title, description, and view count.
2. **Collect songs.** `use_ytdlp.py` (or the older `use_selenium.py`) visits each
   video and reads YouTube's music attribution cards.
3. **Clean and combine.** `utils.py` turns the raw data into the final
   spreadsheet and writes it to `output/`, then copies it to the repo root.

Full setup instructions, script options, and change history are in
[`scripts/README.md`](scripts/README.md).

## Repository layout

```
Callahan_Videos_2026.csv   ← the dataset (download this)
output/                    ← pipeline output (final spreadsheet)
scripts/                   ← all code, playlist list, and pipeline docs
  README.md                ← detailed pipeline documentation
  tempdata/                ← intermediate files (gitignored, except helper script)
```

Bonus: `scripts/create_spotify_playlist.py` turns the song credits from
high-view videos into a Spotify playlist.
