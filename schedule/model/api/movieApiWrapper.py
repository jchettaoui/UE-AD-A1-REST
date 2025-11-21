import requests


class MovieApiWrapper:

    def __init__(self, url_api: str):
        self._url_api : str = url_api

    def get_movie_by_id(self, movie_id: str):
        return requests.get(f"{self._url_api}/movies/{movie_id}")