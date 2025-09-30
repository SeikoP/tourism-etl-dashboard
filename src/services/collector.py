import httpx

class Collector:
    """Simple collector to fetch remote JSON endpoints"""

    def __init__(self, timeout: int = 10):
        self.client = httpx.Client(timeout=timeout)

    def fetch_json(self, url: str):
        r = self.client.get(url)
        r.raise_for_status()
        return r.json()

    def close(self):
        self.client.close()
