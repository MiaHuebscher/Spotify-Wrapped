import matplotlib.pyplot as plt
from spotifyAPI import spotifyAPI
from datetime import datetime
from collections import Counter
from wordcloud import WordCloud


if __name__ == '__main__':
    # Initialize Spotify API class
    spotify = spotifyAPI()

    # Get top listened to artists
    top_artists = spotify.get_top('artists', time_range='long_term', n=5)
    print('Top 5 Artists:')
    for artist in top_artists:
        print(artist['name'])

    # Get top listened to tracks
    top_tracks = spotify.get_top('tracks', time_range='long_term', n=10)
    print('\nTop 10 Tracks:')
    for track in top_tracks:
        print(track['name'])

    # Identify niche tracks in my recent listening
    print('\nNiche Songs from Top 50 Tracks:')
    top_50_tracks = spotify.get_top('tracks', time_range='long_term', n=50)
    niche_songs = spotify.get_niche_songs(top_50_tracks)
    for data in niche_songs:
        print(f'{data["name"]} by {data["artists"][0]["name"]} ({data["popularity"]} popularity)')

    # Identify trends in my saved songs on Spotify
    saved_songs = spotify.get_saved_songs()
    print(f'\n{len(saved_songs)} Saved Songs in My Library')

    # Calculate duration of saved songs
    duration_lst = [dct['track']['duration_ms'] for dct in saved_songs if dct['track']['duration_ms'] != 0]
    duration_ms = sum(duration_lst)
    duration_hrs = duration_ms * (1/3600000)
    print(f'Total Duration of Saved Songs: {round(duration_hrs, 4)} hours')

    # Calculate most common artists in saved songs
    print('The 10 Most Common Artists in Saved Songs:\t')
    artists_frequency = Counter([dct['track']['artists'][0]['name'] for dct in saved_songs])
    sorted_freqs = artists_frequency.most_common(10)
    for i in range(10):
        print(sorted_freqs[i][0])
    print('\nA Wordcloud to visualize how popular certain artists are in my saved songs:')
    wc = WordCloud()
    wc.generate_from_frequencies(frequencies=artists_frequency)
    plt.axis('off')
    plt.imshow(wc)
    plt.show()

    # Calculate and report longest and shortest songs
    longest_song = [i for i, item in enumerate(duration_lst) if item == max(duration_lst)]
    shortest_song = [i for i, item in enumerate(duration_lst) if item == min(duration_lst)]
    print(f'At {round((max(duration_lst)*(1/60000)), 4)} minutes, the longest song(s) in saved songs:')
    for i in longest_song:
        song_info = saved_songs[i]['track']
        print(song_info['name'], 'by', song_info['artists'][0]['name'])
    print(f'\nAt {round((min(duration_lst)*(1/60000)), 4)} minutes, the shortest song(s) in saved songs:')
    for i in shortest_song:
        song_info = saved_songs[i]['track']
        print(song_info['name'], 'by', song_info['artists'][0]['name'])
        
    # Visualize the number of songs added each year to my saved songs
    added_years = [int(dct['added_at'][:4]) for dct in saved_songs]
    year_freqs = Counter(added_years)
    plt.bar(year_freqs.keys(), year_freqs.values())
    # API does not provide a genre for a song, but you can get it for artist
    # and create stack bar chart using artist genres

    # Visualize the frequency of release years in my saved songs
    release_years = [int(dct['track']['album']['release_date'][:4]) for dct in saved_songs if \
                     int(dct['track']['album']['release_date'][:4]) != 0]
    release_freqs = Counter(release_years)
    plt.bar(release_freqs.keys(), release_freqs.values())
    
    # Get the oldest and newest songs in saved songs
    oldest_song = [i for i, item in enumerate(release_years) if item == min(release_years)]
    newest_song = [i for i, item in enumerate(release_years) if item == max(release_years)]
    print('\nOldest Song(s) in Saved Songs:')
    for i in oldest_song:
        song_info = saved_songs[i]['track']
        print(song_info['name'], 'by', song_info['artists'][0]['name'] + f', released in {release_years[i]}')
    print('\nNewest Song(s) in Saved Songs:')
    for i in newest_song:
        song_info = saved_songs[i]['track']
        print(song_info['name'], 'by', song_info['artists'][0]['name'] + f', released in {release_years[i]}')
    # make more granular - month, day    
        
