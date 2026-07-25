#!/usr/bin/env python3
"""MK Studio VPN Service — free public V2Ray config aggregator."""

from __future__ import annotations

import base64
import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.json"
META_FILE = ROOT / "meta.json"
COUNTRIES_DIR = ROOT / "countries"
USER_AGENT = "MK-Studio-VPN-Service/1.0 (+https://github.com/myominn062-svg/mk-studio-vpn-service)"
TIMEOUT = 45
# Aggregator-style caps (publish large lists; no TCP health filter)
MAX_PER_PROTOCOL = 5000
MAX_ALL = 15000
MAX_PER_COUNTRY = 3000

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
FLAG_RE = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")

# ISO2 -> common aliases found in remarks (lowercase)
COUNTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "US": ("united states", "usa", "america"),
    "GB": ("united kingdom", "england", "britain", "uk"),
    "AE": ("united arab emirates", "dubai", "uae"),
    "KR": ("south korea", "korea"),
    "KP": ("north korea",),
    "RU": ("russia", "russian"),
    "DE": ("germany", "deutschland"),
    "FR": ("france",),
    "NL": ("netherlands", "holland"),
    "JP": ("japan", "tokyo", "osaka"),
    "SG": ("singapore",),
    "HK": ("hong kong", "hongkong"),
    "TW": ("taiwan",),
    "CN": ("china",),
    "IN": ("india",),
    "ID": ("indonesia",),
    "MY": ("malaysia",),
    "TH": ("thailand",),
    "VN": ("vietnam", "viet nam"),
    "PH": ("philippines",),
    "AU": ("australia",),
    "CA": ("canada",),
    "BR": ("brazil",),
    "TR": ("turkey", "türkiye", "turkiye"),
    "IR": ("iran", "persian"),
    "IQ": ("iraq",),
    "SA": ("saudi arabia", "saudi"),
    "IL": ("israel",),
    "IT": ("italy",),
    "ES": ("spain",),
    "PT": ("portugal",),
    "PL": ("poland",),
    "SE": ("sweden",),
    "NO": ("norway",),
    "FI": ("finland",),
    "DK": ("denmark",),
    "CH": ("switzerland",),
    "AT": ("austria",),
    "BE": ("belgium",),
    "IE": ("ireland",),
    "CZ": ("czech", "czechia"),
    "RO": ("romania",),
    "BG": ("bulgaria",),
    "HU": ("hungary",),
    "GR": ("greece",),
    "UA": ("ukraine",),
    "KZ": ("kazakhstan",),
    "UZ": ("uzbekistan",),
    "MM": ("myanmar", "burma"),
    "BD": ("bangladesh",),
    "PK": ("pakistan",),
    "NP": ("nepal",),
    "LK": ("sri lanka",),
    "NZ": ("new zealand",),
    "MX": ("mexico",),
    "AR": ("argentina",),
    "CL": ("chile",),
    "CO": ("colombia",),
    "ZA": ("south africa",),
    "EG": ("egypt",),
    "NG": ("nigeria",),
    "KE": ("kenya",),
    "SC": ("seychelles",),
}

# Build reverse lookup: alias/code -> ISO2
_ALIAS_TO_CC: dict[str, str] = {}
for _cc, _aliases in COUNTRY_ALIASES.items():
    _ALIAS_TO_CC[_cc.lower()] = _cc
    for _a in _aliases:
        _ALIAS_TO_CC[_a.lower()] = _cc

# Safe single-token matches only (avoid English words like "in", "no", "me")
_SAFE_SINGLE_TOKENS = sorted(
    {
        *{cc.lower() for cc in COUNTRY_ALIASES},  # ISO2 codes
        "usa",
        "uae",
        "uk",
        "dubai",
        "tokyo",
        "osaka",
        "korea",
        "japan",
        "singapore",
        "germany",
        "france",
        "netherlands",
        "holland",
        "russia",
        "canada",
        "australia",
        "turkey",
        "turkiye",
        "iran",
        "india",
        "china",
        "taiwan",
        "vietnam",
        "thailand",
        "malaysia",
        "indonesia",
        "philippines",
        "myanmar",
        "burma",
        "ukraine",
        "poland",
        "sweden",
        "norway",
        "finland",
        "denmark",
        "switzerland",
        "austria",
        "belgium",
        "ireland",
        "romania",
        "bulgaria",
        "hungary",
        "greece",
        "brazil",
        "mexico",
        "argentina",
        "egypt",
        "israel",
        "saudi",
        "hongkong",
    },
    key=len,
    reverse=True,
)
ISO2_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])("
    + "|".join(re.escape(t) for t in _SAFE_SINGLE_TOKENS)
    + r")(?![A-Za-z0-9])",
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
    for line in text.splitlines():
        line = line.strip().strip("`").strip('"').strip("'")
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if any(lower.startswith(p) for p in PROTOCOL_PREFIXES):
            found.append(line)
            continue
        decoded = try_b64_decode(line)
        if decoded:
            found.extend(extract_uris(decoded))

    for match in URI_RE.findall(text):
        found.append(match.rstrip(").,]}\"'"))

    if not found:
        decoded = try_b64_decode(text)
        if decoded:
            found.extend(extract_uris(decoded))

    return found


def fetch(url: str) -> str:
    """Fetch URL via curl (more reliable than urllib behind local proxies)."""
    import subprocess

    result = subprocess.run(
        [
            "curl",
            "-fsSL",
            "--noproxy",
            "*",
            "-A",
            USER_AGENT,
            "--max-time",
            str(TIMEOUT),
            url,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="ignore").strip() or f"curl exit {result.returncode}"
        raise urllib.error.URLError(err)
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return result.stdout.decode("latin-1", errors="ignore")


def load_sources() -> list[dict]:
    with SOURCES_FILE.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [s for s in payload.get("sources", []) if s.get("enabled", True)]


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_b64(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_text(base64.b64encode(raw).decode("ascii") + "\n", encoding="utf-8")


def flag_to_cc(flag: str) -> str | None:
    if len(flag) != 2:
        return None
    a, b = ord(flag[0]), ord(flag[1])
    if not (0x1F1E6 <= a <= 0x1F1FF and 0x1F1E6 <= b <= 0x1F1FF):
        return None
    return chr(a - 0x1F1E6 + 65) + chr(b - 0x1F1E6 + 65)


def remark_of(uri: str) -> str:
    """Extract human-readable remark/name from a proxy URI."""
    if "#" in uri:
        return urllib.parse.unquote(uri.split("#", 1)[1])
    if uri.lower().startswith("vmess://"):
        payload = uri[8:]
        try:
            raw = base64.b64decode(payload + "=" * (-len(payload) % 4))
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            return str(obj.get("ps") or "")
        except Exception:
            return ""
    return ""


def detect_country(uri: str) -> str | None:
    """Best-effort country ISO2 from remark flag / code / name."""
    text = remark_of(uri)
    if not text:
        return None

    # 1) Flag emoji (highest confidence)
    m = FLAG_RE.search(text)
    if m:
        cc = flag_to_cc(m.group(0))
        if cc:
            return cc

    lower = text.lower()

    # 2) Multi-word aliases first (hong kong, united states, ...)
    for alias, cc in sorted(_ALIAS_TO_CC.items(), key=lambda kv: -len(kv[0])):
        if " " in alias and alias in lower:
            return cc

    # 3) ISO2 / short alias tokens
    for match in ISO2_TOKEN_RE.finditer(text):
        token = match.group(1).lower()
        cc = _ALIAS_TO_CC.get(token)
        if cc:
            return cc

    return None


def main() -> int:
    sources = load_sources()
    collected: list[str] = []
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
                if uri in seen:
                    continue
                seen.add(uri)
                collected.append(uri)
                added += 1
            print(f"[OK] {name}: +{added} unique")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            error = str(exc)
            print(f"[FAIL] {name}: {error}", file=sys.stderr)
        source_stats.append({"name": name, "url": url, "added": added, "error": error})

    print(f"Collected unique: {len(collected)}")

    by_protocol: dict[str, list[str]] = defaultdict(list)
    by_country: dict[str, list[str]] = defaultdict(list)
    unknown_country = 0

    for uri in collected:
        proto = protocol_of(uri)
        if len(by_protocol[proto]) < MAX_PER_PROTOCOL:
            by_protocol[proto].append(uri)
        cc = detect_country(uri)
        if cc:
            if len(by_country[cc]) < MAX_PER_COUNTRY:
                by_country[cc].append(uri)
        else:
            unknown_country += 1

    all_configs: list[str] = []
    # Round-robin across protocols so one type doesn't dominate the published list
    proto_order = ("vless", "vmess", "trojan", "ss", "ssr", "hysteria2", "hysteria", "tuic", "wireguard", "other")
    queues = {p: list(by_protocol.get(p, [])) for p in proto_order}
    while len(all_configs) < MAX_ALL:
        progressed = False
        for p in proto_order:
            if queues[p]:
                all_configs.append(queues[p].pop(0))
                progressed = True
                if len(all_configs) >= MAX_ALL:
                    break
        if not progressed:
            break

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

    write_b64(ROOT / "subscription.txt", all_configs)
    write_b64(ROOT / "subscription-vless.txt", by_protocol.get("vless", []))
    write_b64(ROOT / "subscription-vmess.txt", by_protocol.get("vmess", []))
    write_b64(ROOT / "subscription-trojan.txt", by_protocol.get("trojan", []))
    write_b64(ROOT / "subscription-ss.txt", by_protocol.get("ss", []))

    # Country splits — wipe & recreate so stale countries disappear
    if COUNTRIES_DIR.exists():
        shutil.rmtree(COUNTRIES_DIR, ignore_errors=True)
    COUNTRIES_DIR.mkdir(parents=True, exist_ok=True)

    country_counts: dict[str, int] = {}
    for cc in sorted(by_country.keys()):
        lines = by_country[cc]
        if not lines:
            continue
        write_text(COUNTRIES_DIR / f"{cc}.txt", lines)
        write_b64(COUNTRIES_DIR / f"{cc}.sub.txt", lines)
        country_counts[cc] = len(lines)

    unknown_lines = [u for u in all_configs if detect_country(u) is None][:MAX_PER_COUNTRY]
    if unknown_lines:
        write_text(COUNTRIES_DIR / "UNKNOWN.txt", unknown_lines)
        write_b64(COUNTRIES_DIR / "UNKNOWN.sub.txt", unknown_lines)
        country_counts["UNKNOWN"] = len(unknown_lines)

    index = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "countries": [
            {
                "code": cc,
                "count": country_counts[cc],
                "raw": f"https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/{cc}.txt",
                "subscription": f"https://raw.githubusercontent.com/myominn062-svg/mk-studio-vpn-service/main/countries/{cc}.sub.txt",
            }
            for cc in sorted(country_counts.keys(), key=lambda c: (-country_counts[c], c))
        ],
    }
    (COUNTRIES_DIR / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    readme_lines = [
        "# Countries",
        "",
        "Aggregated free public configs split by country (ISO code).",
        "",
        "Raw: `countries/XX.txt` · Subscription (Base64): `countries/XX.sub.txt`",
        "",
        "| Code | Count | Raw | Subscription |",
        "|------|------:|-----|--------------|",
    ]
    for item in index["countries"]:
        cc = item["code"]
        readme_lines.append(
            f"| {cc} | {item['count']} | "
            f"[`{cc}.txt`](./{cc}.txt) | "
            f"[`{cc}.sub.txt`](./{cc}.sub.txt) |"
        )
    write_text(COUNTRIES_DIR / "README.md", readme_lines)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    meta = {
        "brand": "MK Studio VPN Service",
        "updated_at": now,
        "total_unique_raw": len(collected),
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
            "countries_detected": sum(v for k, v in country_counts.items() if k != "UNKNOWN"),
            "countries_unknown": country_counts.get("UNKNOWN", unknown_country),
            "country_files": len([c for c in country_counts if c != "UNKNOWN"]),
        },
        "countries": country_counts,
        "sources": source_stats,
        "files": {k: len(v) for k, v in outputs.items()},
    }
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Done. published={len(all_configs)} countries={len([c for c in country_counts if c != 'UNKNOWN'])} "
        f"updated_at={now}"
    )
    if len(all_configs) == 0:
        print("WARNING: no configs collected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
