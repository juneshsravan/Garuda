"""
GARUDA Threat Intelligence: Gambling Blocklist Loader
======================================================
Downloads public gambling/betting domain blocklists from curated repositories
(e.g., The Block List Project and StevenBlack hosts gambling extension)
and saves deduplicated registered domains to backend/app/data/gambling_domains.txt.
Optionally syncs domains to the threat_intelligence database table if available.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import logging
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_gambling_blocklist")

DEFAULT_SOURCES = [
    # The Block List Project - Gambling
    "https://raw.githubusercontent.com/blocklistproject/Lists/master/gambling.txt",
    # StevenBlack hosts - Gambling extension
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling/hosts",
]

DEFAULT_OUTPUT_FILE = BACKEND_DIR / "app" / "data" / "gambling_domains.txt"

DOMAIN_REGEX = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$")
IGNORE_HOSTS = {"localhost", "localhost.localdomain", "local", "broadcasthost", "0.0.0.0", "127.0.0.1"}


def is_valid_domain(candidate: str) -> bool:
    if not candidate or len(candidate) > 253:
        return False
    candidate = candidate.lower().rstrip(".")
    if candidate in IGNORE_HOSTS:
        return False
    try:
        ipaddress.ip_address(candidate)
        return False  # Skip raw IPs
    except ValueError:
        pass
    return bool(DOMAIN_REGEX.match(candidate))


def download_source(url: str, timeout: int = 30) -> list[str]:
    logger.info(f"Downloading blocklist from: {url}")
    req = Request(url, headers={"User-Agent": "Garuda-Security-Agent/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            lines = content.splitlines()
            logger.info(f"Downloaded {len(lines)} lines from {url}")
            return lines
    except Exception as exc:
        logger.warning(f"Failed to download from {url}: {exc}")
        return []


def parse_domains_from_lines(lines: list[str]) -> set[str]:
    domains = set()
    for line in lines:
        line = line.strip().lower()
        if not line or line.startswith("#"):
            continue
        # Handle hosts file format (e.g., "0.0.0.0 badsite.com" or "127.0.0.1 badsite.com")
        parts = line.split()
        candidate = parts[-1] if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1") else parts[0]
        candidate = candidate.rstrip(".")
        if is_valid_domain(candidate):
            domains.add(candidate)
    return domains


def save_domains_to_file(domains: set[str], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_domains = sorted(domains)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# GARUDA Gambling Domain Blocklist\n")
        f.write(f"# Total Domains: {len(sorted_domains)}\n\n")
        for d in sorted_domains:
            f.write(f"{d}\n")
    logger.info(f"Saved {len(sorted_domains)} domains to {output_path}")
    return len(sorted_domains)


def sync_to_threat_intelligence(domains: set[str], batch_size: int = 1000) -> int:
    try:
        from app.db.session import check_db_connection, get_session_local
        from app.models.threat import ThreatIntelligence
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        connected, error = check_db_connection()
        if not connected:
            logger.info(f"Database not connected ({error}), skipping threat_intelligence sync.")
            return 0

        logger.info("Syncing gambling domains into threat_intelligence table...")
        SessionLocal = get_session_local()
        inserted_count = 0

        with SessionLocal() as db:
            domain_list = sorted(domains)
            for i in range(0, len(domain_list), batch_size):
                batch = domain_list[i:i + batch_size]
                records = []
                for d in batch:
                    h = hashlib.sha256(d.encode("utf-8")).hexdigest()
                    records.append({
                        "source": "public_gambling_blocklist",
                        "indicator_type": "domain",
                        "indicator_value": d,
                        "indicator_hash": h,
                        "verdict": "gambling",
                    })

                stmt = pg_insert(ThreatIntelligence).values(records)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["source", "indicator_hash"]
                )
                res = db.execute(stmt)
                db.commit()
                inserted_count += (res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(batch))

        logger.info(f"Threat intelligence sync complete ({inserted_count} records processed).")
        return inserted_count
    except Exception as exc:
        logger.warning(f"Could not sync to threat_intelligence table: {exc}")
        return 0


def load_blocklists(
    sources: list[str] | None = None,
    output_file: Path | str | None = None,
    sync_db: bool = True,
) -> int:
    urls = sources or DEFAULT_SOURCES
    out_path = Path(output_file) if output_file else DEFAULT_OUTPUT_FILE

    all_domains: set[str] = set()
    for url in urls:
        lines = download_source(url)
        domains = parse_domains_from_lines(lines)
        logger.info(f"Extracted {len(domains)} valid domains from {url}")
        all_domains.update(domains)

    if not all_domains:
        logger.warning("No domains were extracted from the sources.")
        return 0

    count = save_domains_to_file(all_domains, out_path)

    if sync_db:
        sync_to_threat_intelligence(all_domains)

    return count


def main():
    parser = argparse.ArgumentParser(description="Download public gambling blocklists and save for GARUDA URL analyzer")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Output path for gambling_domains.txt")
    parser.add_argument("--no-db", action="store_true", help="Do not attempt to sync to PostgreSQL database")
    parser.add_argument("--source", action="append", help="Custom blocklist URL (can be specified multiple times)")

    args = parser.parse_args()
    sources = args.source if args.source else DEFAULT_SOURCES
    load_blocklists(sources=sources, output_file=args.output, sync_db=not args.no_db)


if __name__ == "__main__":
    main()
