import requests


class UserApiWrapper:

    def __init__(self, url_api: str):
        self._url_api : str = url_api

    def is_user_an_administrator(self, userid) -> bool:
        if userid is None:
            return False
        result = requests.get(self._url_api+f"/users/{userid}/admin")
        if result.status_code != 200:
            return False
        return result.json()["admin"]
