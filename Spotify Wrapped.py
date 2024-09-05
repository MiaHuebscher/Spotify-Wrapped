import requests
import time
import base64
from urllib.parse import urlencode
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from wordcloud import WordCloud
import matplotlib.pyplot as plt

SCOPE = "user-top-read user-library-read"
REDIRECT_URI = "http://localhost:3000"
AUTH_URL = "https://accounts.spotify.com/authorize?"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOP_URL = "https://api.spotify.com/v1/me/top"
MS_TO_HOURS = 1/3600000


def get_client_credentials():
    with open("Client Credentials.txt", "r") as credentials_file:
        user_id = credentials_file.readline().strip()
        user_secret = credentials_file.readline().strip()
    return user_id, user_secret


def get_login_info():
    with open("Spotify Login.txt") as spotify_file:
        username = spotify_file.readline().strip()
        password = spotify_file.readline().strip()
    return username, password


def get_authorization(user_id, user_username, user_password):
    """Gets the code needed to authorize our access to the user's data"""
    # Configure the authorization details
    auth_headers = {"client_id": user_id,
                    "response_type": "code",
                    "redirect_uri": REDIRECT_URI,
                    "scope": SCOPE}

    # Utilize ChromeDriver to navigate to Spotify API authorization
    service = Service('C:/Program Files/Google/Chrome/Application/chromedriver-win64/chromedriver.exe')
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url=(AUTH_URL + urlencode(auth_headers)))

    # Login to User Spotify
    username = driver.find_element(By.ID, "login-username")
    username.send_keys(user_username)
    password = driver.find_element(By.ID, "login-password")
    password.send_keys(user_password)
    driver.find_element(By.ID, "login-button").click()

    # Get the authorization code
    time.sleep(4)
    refreshed_url = driver.current_url
    code_index = str(refreshed_url).index("code=") + 5
    code = refreshed_url[code_index:]
    return code


def get_access_token(code, credentials):
    """Gets the access token needed to obtain data from the API"""
    token_headers = {"Authorization": "Basic " + credentials,
                     "Content-Type": "application/x-www-form-urlencoded"}

    token_data = {"grant_type": "authorization_code",
                  "code": code,
                  "redirect_uri": "http://localhost:3000"}

    r = requests.post(TOKEN_URL, data=token_data, headers=token_headers)

    token = r.json()["access_token"]
    return token


def get_top(headers, time_range="medium_term", artists=True, tracks=True):

    if artists:
        # Get my top n artists
        n_artists = input("\nEnter the number of top artists you want to see (max of 50): ")
        user_top_artists = requests.get(TOP_URL + "/artists?time_range=" + time_range + "&limit=" + str(n_artists), headers=headers)
        top_artists_info = user_top_artists.json()["items"]

        # Show the results
        print("\nYour top", n_artists, "artists are:")
        for item in top_artists_info:
            print(item["name"])

    if tracks:
        # Get my top n tracks
        n_tracks = input("\nEnter the number of top tracks you want to see (max of 50): ")
        user_top_tracks = requests.get(TOP_URL + "/tracks?time_range=" + time_range + "&limit=" + str(n_tracks), headers=headers)
        top_tracks_info = user_top_tracks.json()["items"]

        # Show the results
        print("\nYour top", n_tracks, "tracks are:")
        for item in top_tracks_info:
            print(item["name"])


def get_all_saved_songs(headers):
    # List of tuples containing the data we want (song, artist, song id, duration in ms)
    saved_songs_lst = []

    # Set offset to 0 (the first fifty items)
    offset = 0
    base_url = "https://api.spotify.com/v1/me/tracks"
    while True:
        url = base_url + "?limit=50&offset=" + str(offset)
        fifty_saved_songs_info = requests.get(url, headers=headers)
        if "items" not in fifty_saved_songs_info.json():
            break
        fifty_items = fifty_saved_songs_info.json()["items"]
        for item in fifty_items:
            song_name = item["track"]["name"]
            artist_name = item["track"]["artists"][0]["name"]
            track_id = item["track"]["id"]
            duration_ms = item["track"]["duration_ms"]

            saved_songs_lst.append((song_name, artist_name, track_id, duration_ms))

        offset += 50

    return saved_songs_lst


def calculate_duration(saved_songs):
    duration_ms = sum([tup[3] for tup in saved_songs])
    duration_hrs = duration_ms * (MS_TO_HOURS)

    return round(duration_hrs, 4)


def get_top_artists(saved_songs, n = 10):
    artists_freqs = Counter([tup[1] for tup in saved_songs])
    sorted_freqs = artists_freqs.most_common(n)
    for i in range(n):
        print(sorted_freqs[i][0])


def find_duration_extrema(saved_songs):
    # Calculate longest and shortest songs
    duration_lst = [tup[3] for tup in saved_songs]
    largest_duration = max(duration_lst)
    smallest_duration = min(duration_lst)
    longest_song_ilst = [i for i, item in enumerate(duration_lst) if item == largest_duration]
    shortest_song_ilst = [i for i, item in enumerate(duration_lst) if item == smallest_duration]

    # Report the longest and shortest songs
    if len(longest_song_ilst) == 1:
        ls_index = longest_song_ilst[0]
        minutes = duration_lst[ls_index] * (1/60000)
        print("\nThe longest song in your saved songs is", saved_songs[ls_index][0], "by", saved_songs[ls_index][1],
              "at", round(minutes, 4), "minutes long")
    else:
        print("You have multiple songs that share the award for longest song in your saved songs. Each of them are",
              round((largest_duration*(1/60000)), 4), "minutes long. Your saved songs with this duration are:")
        for i in longest_song_ilst:
            ls_index = i
            print(saved_songs[ls_index][0], "by", saved_songs[ls_index][1])

    if len(shortest_song_ilst) == 1:
        ls_index = shortest_song_ilst[0]
        minutes = duration_lst[ls_index] * (1/60000)
        print("\nThe shortest song in your playlist is", saved_songs[ls_index][0], "by", saved_songs[ls_index][1],
              "at", round(minutes, 4), "minutes long")
    else:
        print("You have multiple songs that share the award for shortest song in your saved songs. Each of them are",
              round((smallest_duration * (1 / 60000)), 4), "minutes long. Your saved songs with this duration are:")
        for i in shortest_song_ilst:
            ls_index = i
            print(saved_songs[ls_index][0], "by", saved_songs[ls_index][1])


if __name__ == "__main__":
    # Get the Client credentials
    client_id, client_secret = get_client_credentials()
    encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")

    # Get the User's login details
    username, password = get_login_info()

    # Get authorization to access user's data
    auth_code = get_authorization(client_id, username, password)

    # Set the headers needed to get data from the Spotify API
    access_token = get_access_token(auth_code, encoded_credentials)
    user_headers = {"Authorization": "Bearer " + access_token,
                    "Content-Type": "application/json"}

    # Get the top artists and tracks for the user
    term = input("Based on which time range would you like to see your top items ('short', 'medium', or 'long'): ")
    time_term = term + "_term"
    get_top(user_headers, time_range=time_term, artists=True, tracks=True)

    """
    Figure out which artist I have the most liked songs from 
    """
    # Get my saved songs data
    user_saved_songs = get_all_saved_songs(user_headers)

    # Calculate and report data on the user's saved songs
    print("\nHere are some quick stats on your saved songs:\t")
    print("You have", len(user_saved_songs), "saved songs in Spotify")

    total_duration = calculate_duration(user_saved_songs)
    print("The total duration of your saved songs is", total_duration, "hours")

    print("The 10 most common artists in your saved songs are:\t")
    get_top_artists(user_saved_songs, n=10)

    print("\nHere's a Wordcloud to show you how popular certain artists are in your saved songs:")
    artist_freqs = Counter([tup[1] for tup in user_saved_songs])
    wc = WordCloud()
    wc.generate_from_frequencies(frequencies=artist_freqs)
    plt.axis("off")
    plt.imshow(wc)
    plt.show()

    find_duration_extrema(user_saved_songs)









