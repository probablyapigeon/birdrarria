"""Optional localhost client for the shared Lonk/Terraria portal bridge."""
from __future__ import annotations

import json
import socket
from typing import Any


class PortalClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 45871, timeout: float = 0.35):
        self.host = host
        self.port = port
        self.timeout = timeout

    def request(self, *, kind: str, bird: str | None = None, world: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        message = {"version": 1, "kind": kind, "payload": payload or {}}
        if bird is not None:
            message["bird"] = bird
        if world is not None:
            message["world"] = world
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                stream = sock.makefile("rwb")
                stream.write((json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
                stream.flush()
                line = stream.readline(16384)
                return json.loads(line.decode("utf-8")) if line else None
        except (OSError, ValueError, json.JSONDecodeError):
            # The desktop birds remain fully usable when Terraria is closed.
            return None

    def visit(self, bird: str) -> dict[str, Any] | None:
        return self.request(kind="visit", bird=bird, world="desktop")

    def observe(self, bird: str, text: str) -> dict[str, Any] | None:
        return self.request(kind="observe", bird=bird, world="desktop", payload={"text": text})

    def project_progress(self, bird: str, note: str) -> dict[str, Any] | None:
        return self.request(kind="project", bird=bird, world="desktop", payload={"action": "progress", "note": note})

    def approve_build(self, request_id: str) -> dict[str, Any] | None:
        return self.request(kind="build_request", bird="lonk", world="desktop", payload={"action": "approve", "request_id": request_id, "target": "nest", "bounds": {"x": 0, "y": 0, "width": 1, "height": 1}})

