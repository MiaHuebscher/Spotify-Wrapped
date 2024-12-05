import requests
import time
import base64
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class spotifyAPI:
    def __init__(self, scope='user-top-read user-library-read', redirect_uri='http://localhost:3000',
                 user_username=None, user_password=None):
        self.scope = scope
        self.redirect_uri = redirect_uri
        self.headers = spotifyAPI.get_access_headers(self, user_username, user_password)

    @staticmethod
    def get_client_credentials():
        with open("Client Credentials.txt", "r") as credentials_file:
            client_id = credentials_file.readline().strip()
            client_secret = credentials_file.readline().strip()
            encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")
        return client_id, encoded_credentials

    def get_authorization(self, user_username, user_password):
        """Gets the code needed to authorize our access to the user's data"""
        # Get the user information
        user_id, user_credentials = spotifyAPI.get_client_credentials()
        if not user_username and not user_password:
            with open("Spotify Login.txt") as spotify_file:
                user_username = spotify_file.readline().strip()
                user_password = spotify_file.readline().strip()

        # Configure the authorization details
        auth_headers = {"client_id": user_id,
                        "response_type": "code",
                        "redirect_uri": self.redirect_uri,
                        "scope": self.scope}

        # Utilize WebDriver Manager to manage ChromeDriver and navigate to Spotify API authorization
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url=('https://accounts.spotify.com/authorize?' + urlencode(auth_headers)))

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

    def get_access_headers(self, user_username, user_password):
        """Gets the access header needed to obtain data from the API"""
        user_id, user_credentials = spotifyAPI.get_client_credentials()
        token_headers = {"Authorization": "Basic " + user_credentials,
                         "Content-Type": "application/x-www-form-urlencoded"}
        code = spotifyAPI.get_authorization(self, user_username, user_password)
        token_data = {"grant_type": "authorization_code",
                      "code": code,
                      "redirect_uri": self.redirect_uri}

        r = requests.post('https://accounts.spotify.com/api/token', data=token_data, headers=token_headers)
        token = r.json()["access_token"]

        return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

    def get_top(self, item_type, time_range='medium_term', n=10):
        """
        Retrieves the top n specified items
        :param item_type: type of item to return (artists or tracks)
        :param time_range: short_term, medium_term, or long_term
        :param n: number of top item to return
        :return: a dictionary of data for top items
        """
        # Get top n items
        top_items = requests.get(f'https://api.spotify.com/v1/me/top/{item_type}?time_range={time_range}&limit=' +
                                 str(n), headers=self.headers)
        return top_items.json()['items']

    def get_niche_songs(self, song_lst, threshold=60):
        """
        Identifies niche songs from a list of songs with a popularity score below a threshold
        :param song_lst: list of songs to indentify niche songs from
        :param threshold: a score below which to classify songs as niche
        :return: a list of niche songs
        """
        niche_songs = [data for data in song_lst if data['popularity'] < threshold]
        return sorted(niche_songs, key=lambda track: track['popularity'])

    def get_saved_songs(self, offset=0):
        """
        Returns the metadata for tracks saved in the user's Spotify library
        :param offset: the index to start recording saved songs at
        :return: a list of saved songs
        """
        saved_songs = []
        while True:
            url = f'https://api.spotify.com/v1/me/tracks?limit=50&offset={str(offset)}'
            fifty_saved_songs_info = requests.get(url, headers=self.headers)
            if 'items' not in fifty_saved_songs_info.json():
                break
            fifty_items = fifty_saved_songs_info.json()['items']
            saved_songs.extend(fifty_items)
            offset += 50
        return saved_songs
