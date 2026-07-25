#!/usr/bin/env python3
"""MK Studio VPN Service — free public V2Ray config aggregator."""

from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.json"
META_FILE = ROOT / "meta.json"
USER_AGENT = "MK-Studio-VPN-Service/1.0 (+https://github.com/myominn062-svg/mk-studio-vpn-service)"
TIMEOUT = 45
MAX_PER_PROTOCOL = 5000
MAX_ALL = 15000

PROTOCOL_PREFIXES = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "ssr://",
    "hysteria2://",
    "hy2://",
    "hysteria://",
    "tuic://",
    "wireguard://",
)

URI_RE = re.compile(
    r"(?:vmess|vless|trojan|ssr?|hysteria2?|hy2|tuic|wireguard)://[^\s<>\"']+",
    re.IGNORECASE,
)


def protocol_of(uri: str) -> str:
    lower = uri.lower()
    if lower.startswith("vmess://"):
        return "vmess"
    if lower.startswith("vless://"):
        return "vless"
    if lower.startswith("trojan://"):
        return "trojan"
    if lower.startswith("ssr://"):
        return "ssr"
    if lower.startswith("ss://"):
        return "ss"
    if lower.startswith(("hysteria2://", "hy2://")):
        return "hysteria2"
    if lower.startswith("hysteria://"):
        return "hysteria"
    if lower.startswith("tuic://"):
        return "tuic"
    if lower.startswith("wireguard://"):
        return "wireguard"
    return "other"


def looks_valid(uri: str) -> bool:
    if len(uri) < 12 or len(uri) > 8000:
        return False
    if "://" not in uri:
        return False
    # Drop obviously broken fragments
    if " " in uri or "\t" in uri:
        return False
    return True


def try_b64_decode(text: str) -> str | None:
    cleaned = "".join(text.split())
    if len(cleaned) < 16:
        return None
    pad = "=" * (-len(cleaned) % 4)
    for candidate in (cleaned, cleaned + pad):
        try:
            raw = base64.b64decode(candidate, validate=False)
            decoded = raw.decode("utf-8", errors="ignore")
            if any(p in decoded.lower() for p in ("vmess://", "vless://", "trojan://", "ss://")):
                return decoded
        except Exception:
            continue
    return None


def extract_uris(text: str) -> list[str]:
    found: list[str] = []
    # Direct line-by-line (common raw subscription format)
    for line in text.splitlines():
        line = line.strip().strip("`").strip('"').strip("'")
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if any(lower.startswith(p) for p in PROTOCOL_PREFIXES):
            found.append(line)
            continue
        # Maybe whole line is base64 of one or many configs
        decoded = try_b64_decode(line)
        if decoded:
            found.extend(extract_uris(decoded))

    # Regex sweep for mixed HTML/markdown pages
    for match in URI_RE.findall(text):
        found.append(match.rstrip(").,]}\"'"))

    # Whole-body base64 (typical subscription endpoint)
    if not found:
        decoded = try_b64_decode(text)
        if decoded:
            found.extend(extract_uris(decoded))

    return found


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
    # Try utf-8, fall back latin-1
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")


def load_sources() -> list[dict]:
    with SOURCES_FILE.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [s for s in payload.get("sources", []) if s.get("enabled", True)]


def write_text(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_b64(path: Path, lines: list[str]) -> None:
    raw = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_text(base64.b64encode(raw).decode("ascii") + "\n", encoding="utf-8")


def main() -> int:
    sources = load_sources()
    by_protocol: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    source_stats: list[dict] = []

    print(f"Loaded {len(sources)} sources")

    for source in sources:
        name = source.get("name", "unknown")
        url = source["url"]
        added = 0
        error = None
        try:
            body = fetch(url)
            uris = extract_uris(body)
            for uri in uris:
                uri = uri.strip()
                if not looks_valid(uri):
                    continue
                key = uri
                if key in seen:
                    continue
                seen.add(key)
                proto = protocol_of(uri)
                by_protocol[proto].append(uri)
                added += 1
            print(f"[OK] {name}: +{added} unique")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            error = str(exc)
            print(f"[FAIL] {name}: {error}", file=sys.stderr)
        source_stats.append({"name": name, "url": url, "added": added, "error": error})

    # Cap sizes for GitHub friendliness
    for proto, items in list(by_protocol.items()):
        by_protocol[proto] = items[:MAX_PER_PROTOCOL]

    all_configs: list[str] = []
    for proto in ("vless", "vmess", "trojan", "ss", "ssr", "hysteria2", "hysteria", "tuic", "wireguard", "other"):
        all_configs.extend(by_protocol.get(proto, []))
    all_configs = all_configs[:MAX_ALL]

    # Output files (root, like popular public lists)
    outputs = {
        "all_configs.txt": all_configs,
        "MK-Studio-VPN-All-Type.txt": all_configs,
        "vmess_configs.txt": by_protocol.get("vmess", []),
        "vless_configs.txt": by_protocol.get("vless", []),
        "trojan_configs.txt": by_protocol.get("trojan", []),
        "ss_configs.txt": by_protocol.get("ss", []),
        "ssr_configs.txt": by_protocol.get("ssr", []),
        "hysteria2_configs.txt": by_protocol.get("hysteria2", []) + by_protocol.get("hysteria", []),
        "tuic_configs.txt": by_protocol.get("tuic", []),
    }

    for filename, lines in outputs.items():
        write_text(ROOT / filename, lines)

    # Base64 subscription variants (client-friendly)
    write_b64(ROOT / "subscription.txt", all_configs)
    write_b64(ROOT / "subscription-vless.txt", by_protocol.get("vless", []))
    write_b64(ROOT / "subscription-vmess.txt", by_protocol.get("vmess", []))
    write_b64(ROOT / "subscription-trojan.txt", by_protocol.get("trojan", []))
    write_b64(ROOT / "subscription-ss.txt", by_protocol.get("ss", []))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    counts = {k: len(v) for k, v in outputs.items()}
    meta = {
        "brand": "MK Studio VPN Service",
        "updated_at": now,
        "total_unique": len(all_configs),
        "counts": {
            "all": len(all_configs),
            "vmess": len(by_protocol.get("vmess", [])),
            "vless": len(by_protocol.get("vless", [])),
            "trojan": len(by_protocol.get("trojan", [])),
            "ss": len(by_protocol.get("ss", [])),
            "ssr": len(by_protocol.get("ssr", [])),
            "hysteria2": len(by_protocol.get("hysteria2", []) + by_protocol.get("hysteria", [])),
            "tuic": len(by_protocol.get("tuic", [])),
        },
        "sources": source_stats,
        "files": counts,
    }
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Done. total={len(all_configs)} updated_at={now}")
    if len(all_configs) == 0:
        print("WARNING: no configs collected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
