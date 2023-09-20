import requests
import streamlit as st
from auth import Authenticator
from collections import Counter


class Fetcher:
    def __init__(self, auth: Authenticator):
        self.auth = auth

    def fetch_audio_features(self, playlist_id: str):
        @st.cache_data(show_spinner=False)
        def _fetch_audio_features(playlist_id: str):
            token = self.auth.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            playlist_request = requests.get(
                f"https://api.spotify.com/v1/playlists/{playlist_id}", headers=headers
            )
            playlist_name = playlist_request.json()["name"]

            tracks = [
                item["track"] for item in playlist_request.json()["tracks"]["items"]
            ]
            track_info = [
                {
                    "id": track["id"],
                    "artist_id": track["artists"][0]["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "images": track["album"]["images"],
                }
                for track in tracks
            ][:50]
            del tracks

            artist_ids = [track["artist_id"] for track in track_info]
            artists_request = requests.get(
                f'https://api.spotify.com/v1/artists?ids={",".join(artist_ids)}',
                headers=headers,
            )
            for i, artist in enumerate(artists_request.json()["artists"]):
                assert track_info[i]["artist_id"] == artist["id"]
                try:
                    track_info[i]["genre"] = artist["genres"][0]
                except IndexError:
                    track_info[i]["genre"] = self.get_top_genre_of_related_artists(
                        artist["id"]
                    )
                    if track_info[i]["genre"] is None:
                        st.write(track_info[i]["artist"])

            track_ids = [track["id"] for track in track_info]
            tracks_request = requests.get(
                f'https://api.spotify.com/v1/audio-features?ids={",".join(track_ids)}',
                headers=headers,
            )
            for i, features in enumerate(tracks_request.json()["audio_features"]):
                assert track_info[i]["id"] == features["id"]
                track_info[i]["features"] = features

            return {"name": playlist_name, "info": track_info}

        return _fetch_audio_features(playlist_id)

    def get_top_genre_of_related_artists(self, artist_id: str):
        @st.cache_data(show_spinner=False)
        def _get_top_genre_of_related_artists(artist_id: str):
            token = self.auth.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            request = requests.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
                headers=headers,
            )

            genre_counter = Counter()
            for artist in request.json()["artists"]:
                for genre in artist["genres"]:
                    genre_counter[genre] += 1

            return genre_counter.most_common(1)[0][0]

        return _get_top_genre_of_related_artists(artist_id)
