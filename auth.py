import datetime
import os
from base64 import b64encode
from datetime import datetime as dt
from urllib.error import HTTPError

import requests
import streamlit as st

DATE_FORMAT = "%m/%d/%y %H:%M:%S"

class Authenticator:
    def __init__(
        self,
        client_id: str = st.secrets["CLIENT_ID"],
        client_secret: str = st.secrets["CLIENT_SECRET"],
    ) -> str:
        
        self.client_id = client_id
        self.client_secret = client_secret

        if 'token' not in st.session_state:
            self.get_token()

    def get_token(self):
        if (
            'token' in st.session_state
            and 'expiry' in st.session_state
            and dt.now() < st.session_state["expiry"]
        ):
            return st.session_state["token"]

        encoded = b64encode(
            (self.client_id + ":" + self.client_secret).encode("ascii")
        ).decode("ascii")
        headers = {"Authorization": f"Basic {encoded}"}

        request_time = dt.now()
        r = requests.post(
            url="https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers=headers,
        )

        if r.status_code == 200:
            response_data = r.json()
            st.session_state["token"] = response_data["access_token"]
            st.session_state["expiry"] = request_time + datetime.timedelta(
                seconds=response_data["expires_in"]
            )

            return st.session_state["token"]
        else:
            raise HTTPError(
                url="https://accounts.spotify.com/api/token",
                code=r.status_code,
                msg=f"For more info, check out https://developer.spotify.com/documentation/web-api/concepts/api-calls",
                hdrs=headers,
                fp=None,
            )
