import pickle as pkl
from collections import Counter
from urllib.parse import urlparse

import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.elements.progress import ProgressMixin
from sklearn.decomposition import PCA
from auth import Authenticator
from fetcher import Fetcher

LST_FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]

with open("genres.pkl", "rb") as f:
    GENRES = pkl.load(f)

def build_pca_df(playlists: list[dict]):
    dfs = []
    for playlist in playlists:
        features = pd.DataFrame([track["features"] for track in playlist["info"]])
        features = features[LST_FEATURES]
        features["name"] = [track["name"] for track in playlist["info"]]
        features["artist"] = [track["artist"] for track in playlist["info"]]
        features["source"] = playlist["name"]
        features[["genre_1", "genre_2"]] = [
            GENRES[track["genre"]] for track in playlist["info"]
        ]
        dfs.append(features)
    features = pd.concat(dfs, axis=0).reset_index()
    vals = features[LST_FEATURES + ["genre_1", "genre_2"]].values
    vals = (vals - vals.mean(axis=0)) / ((vals.std(axis=0) + 1e-16) ** .75)
    
    tr = pca.fit_transform(vals)

    new_df = pd.DataFrame(tr, columns=["x", "y", "z"])
    new_df["name"] = features["name"]
    new_df["artist"] = features["artist"]
    new_df["source"] = features["source"]

    return new_df

def create_plot_from_features_df(features_df: pd.DataFrame()):
    hovertemplate = "<b>%{customdata[0]}</b><br>" + "%{customdata[1]}"
    fig = px.scatter_3d(
        features_df,
        x="x",
        y="y",
        z="z",
        color="source",
        hover_data={
            "x": False,
            "y": False,
            "z": False,
            "name": True,
            "artist": True,
            "source": False,
        },
        height=800
    )
    fig.update_traces(marker_size=4, hovertemplate=hovertemplate)
    fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig)

if __name__ == "__main__":
    auth = Authenticator()
    pca = PCA(3)
    fetcher = Fetcher(auth)

    st.header("A Spotify Sonic Visualizer")
    st.text("Plots tracks from different playlists based on their sonic attributes.")
    st.text("Hover over each dot to view the song name and artist.")

    playlist_urls = [
        st.text_input(
            label="Playlist URL",
            value="https://open.spotify.com/playlist/4ehHChcQBZTZ0kP9CkHdzc?si=3731045d93c44899",
            placeholder="Paste a link to a cool Spotify playlist!",
        ),
        st.text_input(
            label="Playlist URL",
            value="https://open.spotify.com/playlist/2ZazIXecBCVmTlbyKJHxOc?si=0b3a0267d9b64fc7",
            placeholder="Paste a link to a cool Spotify playlist!",
        ),
        st.text_input(
            label="Playlist URL",
            value="https://open.spotify.com/playlist/1BwLE6QTlmYAtosuvJcgY7?si=ac0da9b6c2e54853",
            placeholder="Paste a link to a cool Spotify playlist!",
        ),
    ]

    while playlist_urls[-1] and len(playlist_urls) < 5:
        playlist_urls.append(
            st.text_input(
                label="Playlist URL", placeholder="Paste a link to a cool Spotify playlist!",
                key = len(playlist_urls)
            )
        )
        
    filled_urls = [url for url in playlist_urls if url]
    
    bar = st.progress(0)
    playlists = []
    for i, url in enumerate(filled_urls):
        bar.progress((i * 50) // len(filled_urls), text="Fetching playlist data...")
        try:
            playlist_id = urlparse(url).path.split("/")[2]
            playlists.append(fetcher.fetch_audio_features(playlist_id))
        except Exception as e:
            raise (e)  # figure this out later
    
    bar.progress(50, text="Computing sonic features...")
    features_df = build_pca_df(playlists)

    bar.progress(80, text="Building plot")
    create_plot_from_features_df(features_df)

    bar.empty()
