"""Shared local protocol for Desktop Lonk birds and Terraria Lonk birds."""
from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = 1
MAX_MESSAGE_BYTES = 16_384
MAX_TEXT = 240
BIRDS = frozenset({"lonk", "pip"})
WORLDS = frozenset({"desktop", "terraria"})
KINDS = frozenset({"hello", "observe", "visit", "teach", "project", "build_request"})
BUILD_ACTIONS = frozenset({"propose", "approve", "reject"})


def _text(value: Any, field: str, limit: int = MAX_TEXT) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return value


def validate_message(message: Any) -> dict[str, Any]:
    if not isinstance(message, dict):
        raise ValueError("message must be an object")
    if message.get("version") != PROTOCOL_VERSION:
        raise ValueError("unsupported protocol version")
    kind = message.get("kind")
    if kind not in KINDS:
        raise ValueError("unknown message kind")
    bird = message.get("bird")
    if bird is not None and bird not in BIRDS:
        raise ValueError("unknown bird")
    world = message.get("world")
    if world is not None and world not in WORLDS:
        raise ValueError("unknown world")
    payload = message.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    clean = {"version": PROTOCOL_VERSION, "kind": kind}
    if bird is not None:
        clean["bird"] = bird
    if world is not None:
        clean["world"] = world
    clean["payload"] = payload
    if kind in {"observe", "teach"}:
        clean["payload"] = dict(payload)
        clean["payload"]["text"] = _text(payload.get("text"), "payload.text")
    if kind == "project" and "action" in payload:
        clean["payload"] = dict(payload)
        clean["payload"]["action"] = _text(payload["action"], "payload.action", 48)
    if kind == "build_request":
        action = payload.get("action", "propose")
        if action not in BUILD_ACTIONS:
            raise ValueError("unsupported build action")
        clean["payload"] = dict(payload)
        clean["payload"]["action"] = action
        clean["payload"]["target"] = _text(payload.get("target"), "payload.target", 48)
        bounds = payload.get("bounds")
        if not isinstance(bounds, dict):
            raise ValueError("payload.bounds must be an object")
        required = ("x", "y", "width", "height")
        if any(type(bounds.get(key)) is not int for key in required):
            raise ValueError("build bounds must use integer x, y, width, height")
        if bounds["width"] < 1 or bounds["width"] > 20 or bounds["height"] < 1 or bounds["height"] > 20:
            raise ValueError("build bounds must be between 1 and 20 blocks")
        if abs(bounds["x"]) > 1_000_000 or abs(bounds["y"]) > 1_000_000:
            raise ValueError("build bounds are outside the allowed world range")
        clean["payload"]["bounds"] = dict(bounds)
        if "request_id" in payload:
            clean["payload"]["request_id"] = _text(payload["request_id"], "payload.request_id", 64)
    return clean


def encode(message: dict[str, Any]) -> bytes:
    clean = validate_message(message)
    raw = (json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ValueError("message exceeds maximum size")
    return raw


def decode(line: bytes | str) -> dict[str, Any]:
    if isinstance(line, str):
        line = line.encode("utf-8")
    if len(line) > MAX_MESSAGE_BYTES:
        raise ValueError("message exceeds maximum size")
    return validate_message(json.loads(line))
