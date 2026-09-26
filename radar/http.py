"""HTTP helpers: browser-like user agent (several news sites reject scripts) and simple retries."""
import time

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"})


def request(method: str, url: str, retries: int = 2, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", 30)
    for attempt in range(retries + 1):
        try:
            response = session.request(method, url, **kwargs)
            if response.status_code == 429 and attempt < retries:  # rate limited: back off, retry
                time.sleep(5 * (attempt + 1))
                continue
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def get_json(url: str, **kwargs):
    return request("GET", url, **kwargs).json()


def get_bytes(url: str, **kwargs) -> bytes:
    return request("GET", url, **kwargs).content


def post_json(url: str, payload: dict, **kwargs):
    return request("POST", url, json=payload, **kwargs).json()
