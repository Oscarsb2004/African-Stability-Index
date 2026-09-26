"""The network transport readers fetch through. TLS verification is always on."""

from __future__ import annotations

import urllib.request

USER_AGENT = "athena-data/0.1 (research replication; private use)"


class HttpTransport:
    def __init__(self, timeout: float = 120.0, user_agent: str = USER_AGENT):
        self.timeout = timeout
        self.user_agent = user_agent

    def get(self, url: str) -> tuple[bytes, str]:
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read(), response.headers.get_content_type()


class FixtureTransport:
    """Serves bytes from a dictionary, so tests never touch the network."""

    def __init__(self, files: dict[str, bytes], media_type: str = "application/octet-stream"):
        self.files = files
        self.media_type = media_type
        self.requested: list[str] = []

    def get(self, url: str) -> tuple[bytes, str]:
        self.requested.append(url)
        if url not in self.files:
            raise KeyError(f"no fixture for {url}")
        return self.files[url], self.media_type
