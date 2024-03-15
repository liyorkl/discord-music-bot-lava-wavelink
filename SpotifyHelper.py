import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import secrets_me

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=secrets_me.spotifyID,
                                                                              client_secret=secrets_me.spotifySecret))


def searcher(query):
    search = spotify.search(query)
    print(search["tracks"]["items"][0]["external_urls"]["spotify"])
    return search["tracks"]["items"][0]["external_urls"]["spotify"]
