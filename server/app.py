#!/usr/bin/env python3
"""Serve a private Hysteria 2 subscription with KiwiVM usage metadata."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

CONFIG_DIR = Path(os.environ.get("KIWISUB_CONFIG_DIR", "/etc/kiwivm-subscription"))
STATE_FILE = Path(
    os.environ.get(
        "KIWISUB_STATE_FILE",
        "/var/lib/kiwivm-subscription/usage-cache.json",
    )
)
API_URL = os.environ.get(
    "KIWISUB_API_URL",
    "https://api.64clouds.com/v1/getServiceInfo",
)
CACHE_SECONDS = int(os.environ.get("KIWISUB_CACHE_SECONDS", "300"))
STALE_CACHE_SECONDS = int(os.environ.get("KIWISUB_STALE_CACHE_SECONDS", "86400"))
LISTEN_ADDRESS = os.environ.get("KIWISUB_LISTEN_ADDRESS", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("KIWISUB_LISTEN_PORT", "18080"))
DISPLAY_TIMEZONE = os.environ.get("KIWISUB_TIMEZONE", "Asia/Shanghai")


def read_value(name: str) -> str:
    """Read a trimmed, root-managed value from the service config directory."""
    return (CONFIG_DIR / name).read_text(encoding="utf-8").strip()


def load_cache() -> dict | None:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_cache(payload: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(STATE_FILE)


def fetch_usage() -> dict:
    """Fetch quota data from KiwiVM, falling back to a recent local cache."""
    cached = load_cache()
    now = int(time.time())
    if cached and now - int(cached.get("fetched_at", 0)) < CACHE_SECONDS:
        return cached

    post_data = urllib.parse.urlencode(
        {"veid": read_value("veid"), "api_key": read_value("api_key")}
    ).encode("ascii")
    request = urllib.request.Request(
        API_URL,
        data=post_data,
        headers={"User-Agent": "KiwiVM-Hysteria2-Subscription/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if str(result.get("error", "0")) not in ("0", "None", ""):
            raise RuntimeError("KiwiVM API returned an error")

        multiplier = Decimal(str(result.get("monthly_data_multiplier", 1)))
        payload = {
            "fetched_at": now,
            "total": int(Decimal(str(result["plan_monthly_data"])) * multiplier),
            "used": int(Decimal(str(result["data_counter"])) * multiplier),
            "reset": int(result["data_next_reset"]),
        }
        save_cache(payload)
        return payload
    except Exception:
        if cached and now - int(cached.get("fetched_at", 0)) < STALE_CACHE_SECONDS:
            return cached
        raise


def build_subscription(usage: dict) -> tuple[bytes, int, int]:
    """Build a standard Base64 node subscription and usage headers."""
    total = max(int(usage["total"]), 0)
    used = max(int(usage["used"]), 0)
    remaining = max(total - used, 0)
    try:
        display_timezone = ZoneInfo(DISPLAY_TIMEZONE)
    except ZoneInfoNotFoundError:
        # Minimal Windows/Python environments may not bundle the IANA tzdata.
        display_timezone = timezone.utc
    reset = datetime.fromtimestamp(int(usage["reset"]), display_timezone)
    node_name = read_value("node_name") or "Bandwagon"
    country_emoji = read_value("country_emoji")
    prefix = f"{country_emoji} " if country_emoji else ""
    label = (
        f"{prefix}{node_name}｜余{remaining / 1_000_000_000:.1f}G"
        f"｜{reset:%m-%d}重置"
    )

    node_uri = read_value("node_uri").split("#", 1)[0]
    renamed_uri = node_uri + "#" + urllib.parse.quote(label, safe="")
    body = base64.b64encode((renamed_uri + "\n").encode("utf-8")) + b"\n"
    return body, used, total


class SubscriptionHandler(BaseHTTPRequestHandler):
    server_version = "PrivateSubscription"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        expected_path = "/sub/" + read_value("token")
        if urllib.parse.urlsplit(self.path).path != expected_path:
            self.send_error(404)
            return
        try:
            body, used, total = build_subscription(fetch_usage())
        except Exception:
            self.send_error(503, "Usage data temporarily unavailable")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "subscription-userinfo",
            f"upload=0; download={used}; total={total}",
        )
        self.send_header("profile-update-interval", "6")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((LISTEN_ADDRESS, LISTEN_PORT), SubscriptionHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
