import requests


class ScheduleApiWrapper:
    
    def __init__(self, url_api: str):
        self._url_api : str = url_api

    def is_movie_scheduled(self, date: str, movie_id: str):
        return requests.get(f"{self._url_api}/schedule/{date}/{movie_id}")
