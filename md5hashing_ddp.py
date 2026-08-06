"""Minimal Meteor DDP client for md5hashing.net (WebSocket + SockJS fallback)."""
from __future__ import annotations

import json
import random
import string
import time
import urllib.error
import urllib.request
from typing import Any

try:
    import websocket  # websocket-client
except ImportError as exc:
    raise SystemExit("pip install websocket-client") from exc

BASE = "https://md5hashing.net"
WS_URL = "wss://md5hashing.net/websocket"


def _rand_id(n: int = 17) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


class DDPClient:
    def __init__(self, url: str = WS_URL) -> None:
        self.url = url
        self.ws: websocket.WebSocket | None = None
        self._pending: dict[str, Any] = {}

    def connect(self) -> None:
        headers = [
            "Origin: https://md5hashing.net",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ]
        self.ws = websocket.create_connection(
            self.url,
            subprotocols=["ddp"],
            timeout=30,
            header=headers,
        )
        self._send({"msg": "connect", "version": "1", "support": ["1", "pre2", "pre1"]})
        deadline = time.time() + 20
        while time.time() < deadline:
            msg = self._recv()
            if msg.get("msg") == "connected":
                return
            if msg.get("msg") == "failed":
                raise RuntimeError(f"DDP connect failed: {msg}")
        raise TimeoutError("DDP connect timeout")

    def call(self, method: str, params: list[Any], timeout: float = 30.0) -> Any:
        if not self.ws:
            raise RuntimeError("not connected")
        mid = _rand_id()
        self._send({"msg": "method", "method": method, "params": params, "id": mid})
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self._recv()
            if msg.get("msg") == "result" and msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(json.dumps(msg["error"]))
                return msg.get("result")
        raise TimeoutError(f"method {method} timeout")

    def close(self) -> None:
        if self.ws:
            self.ws.close()
            self.ws = None

    def _send(self, obj: dict[str, Any]) -> None:
        assert self.ws is not None
        self.ws.send(json.dumps(obj))

    def _recv(self) -> dict[str, Any]:
        assert self.ws is not None
        raw = self.ws.recv()
        return json.loads(raw)


def decode_hash(hash_type: str, digest: str) -> Any:
    """Reverse lookup via hash.get (same as site decode page)."""
    client = DDPClient()
    try:
        client.connect()
        return client.call("hash.get", [hash_type, digest.lower()])
    finally:
        client.close()


def decode_batch(hash_type: str, digests: list[str]) -> Any:
    client = DDPClient()
    try:
        client.connect()
        return client.call("massDecode", [hash_type, [d.lower() for d in digests]])
    finally:
        client.close()


if __name__ == "__main__":
    import sys

    htype = sys.argv[1] if len(sys.argv) > 1 else "md5"
    hval = sys.argv[2] if len(sys.argv) > 2 else "5d41402abc4b2a76b9719d911017c592"
    print(json.dumps(decode_hash(htype, hval), indent=2))
