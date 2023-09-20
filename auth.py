import datetime
import os
from base64 import b64encode
from datetime import datetime as dt
from urllib.error import HTTPError

import dotenv
import requests

ENV_PATH = "./.env"
DATE_FORMAT = "%m/%d/%y %H:%M:%S"
dotenv.load_dotenv(ENV_PATH)

class Authenticator:
    def __init__(
        self,
        client_id: str = os.getenv("CLIENT_ID"),
        client_secret: str = os.getenv("CLIENT_SECRET"),
        token: str = os.getenv("TOKEN"),
        expiry: str = os.getenv("EXPIRY"),
    ) -> str:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self.expiry = dt.strptime(expiry, DATE_FORMAT) if expiry else None

    def get_token(self):
        if (
            self.token is not None
            and self.expiry is not None
            and dt.now() < self.expiry
        ):
            return self.token

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
            self.token = response_data["access_token"]
            self.expiry = request_time + datetime.timedelta(
                seconds=response_data["expires_in"]
            )

            dotenv.set_key(ENV_PATH, key_to_set="TOKEN", value_to_set=self.token)
            dotenv.set_key(
                ENV_PATH,
                key_to_set="EXPIRY",
                value_to_set=dt.strftime(self.expiry, DATE_FORMAT),
            )

            return self.token
        else:
            raise HTTPError(
                url="https://accounts.spotify.com/api/token",
                code=r.status_code,
                msg=f"For more info, check out https://developer.spotify.com/documentation/web-api/concepts/api-calls",
                hdrs=headers,
                fp=None,
            )
