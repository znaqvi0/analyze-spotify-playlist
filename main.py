import matplotlib
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import matplotlib.pyplot as plt
from collections import defaultdict
import random
from tkinter import *
from secret_variables import SPOTIFY_CLIENT_SECRET, SPOTIFY_CLIENT_ID


def authenticate(client_id, client_secret):
    # Authenticate with Spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp


def get_playlist_id(playlist_url):
    # Get the playlist ID from the URL
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    return playlist_id


def get_data(sp, playlist_id):
    # must be stored in advance or else functions will call the api every time, slowing the program
    data = sp.playlist_items(playlist_id, fields='items.track.artists.name,items.track.duration_ms,next', limit=100)
    return data


def get_playlist_name(sp, id_playlist):
    playlist = sp.playlist(id_playlist)
    return playlist['name']


def get_artists_and_durations(data):
    # Get the tracks in the playlist
    results = data
    tracks = results['items']

    # Create an array to store the artist names and track durations
    artists_and_durations = []

    # Loop through each track and add the artist name and track duration to the array
    for track in tracks:
        artist_name = track['track']['artists'][0]['name'].replace("$", "\\$")
        artists_and_durations.append((artist_name, track['track']['duration_ms']))

    # Continue retrieving tracks until there are no more pages
    while results['next']:
        results = sp.next(results)
        tracks = results['items']
        for track in tracks:
            artist_name = track['track']['artists'][0]['name'].replace("$", "\\$")
            artists_and_durations.append((artist_name, track['track']['duration_ms']))

    # Print the array of artist names and track durations
    return artists_and_durations


def get_unique_artists(artists_and_durations):
    # Create a set to store the unique artist names
    unique_artists = set()

    # Loop through each track and add the artist name to the set
    for artist, _ in artists_and_durations:
        unique_artists.add(artist)

    # Return the set of unique artist names as a list
    return list(unique_artists)


def get_proportions_per_artist_minutes(artists_durations, is_sorted=False):
    result = []

    total_duration_ms = 0
    duration_per_artist_ms = defaultdict(int)

    for artist, duration_ms in artists_durations:
        total_duration_ms += duration_ms
        duration_per_artist_ms[artist] += duration_ms

    for artist, duration_ms in duration_per_artist_ms.items():
        proportion = duration_ms / total_duration_ms
        result.append([artist, proportion])

    if is_sorted:
        # Sort the result by the proportion from least to greatest
        result.sort(key=lambda x: x[1])
    return result


def get_proportions_per_artist_songs(artists_durations, is_sorted=False):
    # artists_durations contains a list of [artist, duration_ms] per track in playlist
    result = []

    total_songs = 0
    songs_per_artist = defaultdict(int)

    for artist, duration_ms in artists_durations:
        total_songs += 1
        songs_per_artist[artist] += 1

    for artist, num_songs in songs_per_artist.items():
        proportion = num_songs / total_songs
        result.append([artist, proportion])

    if is_sorted:
        # Sort the result by the proportion from least to greatest
        result.sort(key=lambda x: x[1])
    return result


def get_total_ms(artists_durations):
    total = 0
    for _, duration in artists_durations:
        total += duration
    return total


def make_chart(chart_data, num_top_artists, is_sorted, window_title):
    labels = []
    sizes = []
    other_sum = 0

    # Sort the chart data by the proportion from greatest to least
    chart_data.sort(key=lambda x: x[1], reverse=True)

    # Only show the top num_top_artists artists and their percentages
    for item in chart_data[:num_top_artists]:
        labels.append(item[0])
        sizes.append(item[1])

    # Put the rest in the "Other" category
    for item in chart_data[num_top_artists:]:
        other_sum += item[1]

    if other_sum > 0:
        labels.append('Other')
        sizes.append(other_sum)

    # Randomize the positions of the wedges if is_sorted is False
    if not is_sorted:
        zipped = list(zip(labels, sizes))
        random.shuffle(zipped)
        labels, sizes = zip(*zipped)

    # plt.style.use('dark_background')
    # maybe make percentage text smaller/thinner?
    fig1, ax1 = plt.subplots()
    colors = matplotlib.cm.rainbow(np.linspace(0, 1, len(labels)))
    # remove colors parameter for normal colors
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=135, textprops={'fontsize': 9}, colors=colors)
    ax1.axis('equal')

    plt.title(window_title)
    plt.show()


# Set your client ID and client secret
client_id = SPOTIFY_CLIENT_ID
client_secret = SPOTIFY_CLIENT_SECRET

sp = authenticate(client_id, client_secret)
# Create the main window
root = Tk()
root.title("Spotify Playlist Analyzer")

# Create the labels and entry fields
playlist_url_label = Label(root, text="Enter the Spotify playlist URL:")
playlist_url_entry = Entry(root)

num_top_artists_label = Label(root, text="Enter the number of top artists to show:")
num_top_artists_entry = Entry(root)

sorted_label = Label(root, text="Sort the chart by proportion:")
sorted_var = IntVar()
sorted_checkbox = Checkbutton(root, variable=sorted_var)

by_minutes_label = Label(root, text="Use song minutes instead of number of songs: ")
by_minutes_var = IntVar()
by_minutes_checkbox = Checkbutton(root, variable=by_minutes_var)

# Create the submit button
submit_button = Button(root, text="Submit", command=lambda: submit())

widgets = [playlist_url_label, playlist_url_entry,
           num_top_artists_label, num_top_artists_entry,
           by_minutes_label, by_minutes_checkbox,
           sorted_label, sorted_checkbox,
           submit_button]

# Pack the widgets
# playlist_url_label.pack()
# playlist_url_entry.pack()
#
# num_top_artists_label.pack()
# num_top_artists_entry.pack()
#
# by_minutes_label.pack()
# by_minutes_checkbox.pack()
#
# sorted_label.pack()
# sorted_checkbox.pack()
#
# submit_button.pack()
for widget in widgets:
    widget.pack()


def submit():
    # Get the values from the entry fields
    playlist_url = playlist_url_entry.get()
    num_top_artists = int(num_top_artists_entry.get())
    sorted_value = bool(sorted_var.get())

    by_minutes = bool(by_minutes_var.get())

    # Get the data from Spotify
    playlist_id = get_playlist_id(playlist_url)
    data = get_data(sp, playlist_id)

    artists_and_durations = get_artists_and_durations(data)
    unique_artists = get_unique_artists(artists_and_durations)
    playlist_name = get_playlist_name(sp, playlist_id)
    total_minutes = round(get_total_ms(artists_and_durations)/1000/60)
    num_songs = len(artists_and_durations)
    num_unique_artists = len(unique_artists)

    if by_minutes:
        chart_data = get_proportions_per_artist_minutes(artists_and_durations, sorted_value)
    else:
        chart_data = get_proportions_per_artist_songs(artists_and_durations, sorted_value)

    # Make the chart
    title = f"{playlist_name}: {total_minutes} minutes, {num_songs} songs, {num_unique_artists} unique artists"
    make_chart(chart_data, num_top_artists=num_top_artists, is_sorted=sorted_value, window_title=title)


# Run the main loop
root.mainloop()
