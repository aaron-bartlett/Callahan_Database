import csv
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import read_playlists, tempdata

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


def get_playlist_video_urls(driver, playlist_id):
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    driver.get(playlist_url)

    # Handle the "Cookie/Consent" popup if it appears
    try:
        consent_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@aria-label='Accept the use of cookies and other data for the purposes described']")))
        consent_btn.click()
    except Exception:
        pass  # Popup didn't appear

    # Scroll to load all videos
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)  # Small sleep is okay here to let the scroll "settle"
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    video_links = driver.find_elements(By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer")
    return [link.get_attribute("href") for link in video_links]


def scrape_songs_for_video(driver, wait):
    try:
        # Scroll down slightly to trigger the metadata load
        driver.execute_script("window.scrollBy(0, 500);")

        # Wait for the metadata container to exist
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yt-video-attribute-view-model__title")))

        songs_elements = driver.find_elements(By.CLASS_NAME, "yt-video-attribute-view-model__title")

        songs_found = []
        for el in songs_elements:
            # Use textContent instead of .text because .text returns "" if the element
            # is considered "not visible" by Selenium's strict standards.
            song_name = el.get_attribute("textContent").strip()
            if song_name:
                songs_found.append(song_name)

        if not songs_found:
            # Fallback: Sometimes titles are in a different class depending on the layout version
            alt_elements = driver.find_elements(By.CSS_SELECTOR, "h3.yt-video-attribute-view-model__title")
            songs_found = [e.get_attribute("textContent").strip() for e in alt_elements if e.get_attribute("textContent")]

        return "|".join(songs_found)

    except Exception:
        return "No Songs Detected"


if len(sys.argv) == 1:
    playlists = [input('Paste Playlist ID: ')]
elif sys.argv[1] == '--all':
    playlists = read_playlists()
else:
    playlists = [sys.argv[1]]

options = Options()
options.add_argument("--headless=new")  # Run in background
options.add_argument("--mute-audio")    # Don't play video sound while scraping

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)  # Set a global max wait of 10 seconds

ids_set = load_scraped_ids()

with open(songs_path, 'a', newline='', encoding='utf-8') as songsfile:
    songs_writer = csv.writer(songsfile)

    for i, playlist_id in enumerate(playlists, 1):
        print(f"[{i}/{len(playlists)}] Playlist {playlist_id}")

        try:
            video_urls = get_playlist_video_urls(driver, playlist_id)
        except Exception as e:
            print(f"  Skipping playlist {playlist_id}: {e}")
            continue

        for url in video_urls:
            video_id = url.split('&')[0].split('=')[-1]
            if video_id in ids_set:
                continue
            ids_set.add(video_id)

            driver.get(url)
            songs = scrape_songs_for_video(driver, wait)

            print(f"ID: {video_id} | Songs: {songs}")
            songs_writer.writerow([video_id, songs])
            songsfile.flush()  # persist progress as we go, in case a later playlist/video fails

driver.quit()
