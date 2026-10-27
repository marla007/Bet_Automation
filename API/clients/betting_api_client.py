"""Client for the betting API: one method per endpoint.

Methods return the raw response, so tests can check status codes and error bodies.
"""

import requests


class BettingApiClient:
    def __init__(self, base_url, user_id):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers["x-user-id"] = user_id

    def get_matches(self):
        return self.session.get(f"{self.base_url}/api/matches")

    def get_balance(self):
        return self.session.get(f"{self.base_url}/api/balance")

    def place_bet(self, payload):
        return self.session.post(f"{self.base_url}/api/place-bet", json=payload)

    def reset_balance(self):
        return self.session.post(f"{self.base_url}/api/reset-balance")

    def close(self):
        self.session.close()
