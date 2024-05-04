from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import re
import csv
import sys


chromedriver = "/Users/aaron/Documents/Callahan_Data/chromedriver-mac-arm64/chromedriver"

service = Service(chromedriver)  # Replace 'path_to_chromedriver.exe' with the path to your chromedriver executable
options = Options()
options.headless = True  # Run Chrome in headless mode
driver = webdriver.Chrome(service=service, options=options)

if len(sys.argv) == 1:
    playlist_id = input('Paste Playlist ID: ')
else:
    playlist_id = sys.argv[1]

# URL of the YouTube playlist
playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

# Open the playlist URL
driver.get(playlist_url)
time.sleep(5)  # Allow some time for the page to load

# Scroll to the bottom of the page to load all videos
last_height = driver.execute_script("return document.documentElement.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(2)  # Adjust the time delay as needed
    new_height = driver.execute_script("return document.documentElement.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Get video links
video_links = driver.find_elements(By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer")

# Extract video URLs
video_urls = [link.get_attribute("href") for link in video_links]

with open("temp_songs.csv", 'a', newline='') as songsfile:
    songs_writer = csv.writer(songsfile)

    # Visit each video URL and get the title
    for url in video_urls:
        video_id = url.split('&', 1)[0].split('=', 1)[1]
        driver.get(url)
        time.sleep(2)  # Adjust the time delay as needed
        try:
            songs_set = set()
            songs_element = driver.find_elements(By.CLASS_NAME, "yt-video-attribute-view-model__title")
            for single_element in songs_element:
                html_content = single_element.get_attribute('outerHTML')
                #print("HTML content of the element:", html_content)
                song = re.sub(r'<[^>]+>', '', html_content)
                songs_set.add(song)
                
            print("Songs:", songs_set)
            songs_writer.writerow([video_id, songs_set])

        except Exception as e:
            print("No Songs Detected", e)
            songs_writer.writerow([video_id, "No Songs Detected"])

# Quit the WebDriver
driver.quit()