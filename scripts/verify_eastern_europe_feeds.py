#!/usr/bin/env python3
"""
Live feed verification for Eastern Europe / Russia / Belarus sources.

Requires internet access. Run with:
    python scripts/verify_eastern_europe_feeds.py

Exit code 0 = all feeds passed. Non-zero = at least one feed failed.
"""

import sys
import time
import json

sys.path.insert(0, ".")

from config.settings import Config
from src.scraper import ArticleScraper

EASTERN_EUROPE_FEEDS = [
    "moscow_times",
    "meduza_en",
    "kyiv_independent",
    "politico_europe",
    "notes_from_poland",
    "emerging_europe",
    "balkan_insight",
    "intellinews",
    "euromaidanpress",
    "novaya_gazeta_europe",
]

REQUIRED_FIELDS = {"title", "url", "published", "summary", "source", "tags", "image"}
WARN_FIELDS = {"published", "summary", "image"}  # Missing these is OK but noteworthy

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_field(article, field):
    val = article.get(field)
    if field == "tags":
        return isinstance(val, list)
    return bool(val and str(val).strip())


def verify_feed(scraper, key, url):
    articles = scraper.get_rss_articles(url)

    if not articles:
        return {
            "status": "FAIL",
            "reason": "returned 0 articles",
            "count": 0,
        }

    sample = articles[:5]
    field_stats = {}
    for field in REQUIRED_FIELDS:
        filled = sum(1 for a in sample if check_field(a, field))
        field_stats[field] = {"filled": filled, "total": len(sample)}

    missing_critical = [
        f for f in REQUIRED_FIELDS - WARN_FIELDS
        if field_stats[f]["filled"] == 0
    ]
    missing_warn = [
        f for f in WARN_FIELDS
        if field_stats[f]["filled"] == 0
    ]
    partial_warn = [
        f for f in WARN_FIELDS
        if 0 < field_stats[f]["filled"] < len(sample)
    ]

    status = "FAIL" if missing_critical else ("WARN" if (missing_warn or partial_warn) else "OK")

    first = articles[0]
    return {
        "status": status,
        "count": len(articles),
        "field_stats": field_stats,
        "missing_critical": missing_critical,
        "missing_warn": missing_warn,
        "partial_warn": partial_warn,
        "sample_title": first.get("title", "")[:80],
        "sample_url": first.get("url", "")[:80],
        "has_image": bool(first.get("image")),
    }


def print_result(key, url, result):
    status = result["status"]
    color = GREEN if status == "OK" else (YELLOW if status == "WARN" else RED)
    icon = "✓" if status == "OK" else ("⚠" if status == "WARN" else "✗")

    print(f"\n{BOLD}{color}{icon} {key}{RESET}")
    print(f"  URL   : {url}")

    if status == "FAIL" and "reason" in result:
        print(f"  {RED}REASON : {result['reason']}{RESET}")
        return

    print(f"  Count : {result['count']} articles")
    print(f"  Title : {result.get('sample_title', 'N/A')}")
    print(f"  Link  : {result.get('sample_url', 'N/A')}")
    print(f"  Image : {'yes' if result.get('has_image') else 'no'}")

    if result.get("missing_critical"):
        print(f"  {RED}MISSING (critical): {result['missing_critical']}{RESET}")
    if result.get("missing_warn"):
        print(f"  {YELLOW}MISSING (warn): {result['missing_warn']}{RESET}")
    if result.get("partial_warn"):
        print(f"  {YELLOW}PARTIAL: {result['partial_warn']}{RESET}")

    stats = result.get("field_stats", {})
    if stats:
        row = "  Fields: " + "  ".join(
            f"{f}={v['filled']}/{v['total']}" for f, v in stats.items()
        )
        print(row)


def main():
    print(f"{BOLD}=== Eastern Europe Feed Verification ==={RESET}")
    print(f"Testing {len(EASTERN_EUROPE_FEEDS)} feeds against schema:\n"
          f"  required : {sorted(REQUIRED_FIELDS)}\n")

    scraper = ArticleScraper()
    results = {}
    failed = []
    warned = []

    for key in EASTERN_EUROPE_FEEDS:
        url = Config.RSS_FEEDS.get(key)
        if not url:
            print(f"{RED}✗ {key}: not found in Config.RSS_FEEDS{RESET}")
            failed.append(key)
            continue

        result = verify_feed(scraper, key, url)
        results[key] = result
        print_result(key, url, result)

        if result["status"] == "FAIL":
            failed.append(key)
        elif result["status"] == "WARN":
            warned.append(key)

        time.sleep(1)

    print(f"\n{BOLD}=== Summary ==={RESET}")
    total = len(EASTERN_EUROPE_FEEDS)
    ok_count = total - len(failed) - len(warned)
    print(f"  {GREEN}OK  : {ok_count}/{total}{RESET}")
    print(f"  {YELLOW}WARN: {len(warned)}/{total}  {warned}{RESET}")
    print(f"  {RED}FAIL: {len(failed)}/{total}  {failed}{RESET}")

    if failed:
        print(f"\n{RED}Action needed: remove or replace failing feeds before deploying.{RESET}")
        return 1
    if warned:
        print(f"\n{YELLOW}Review warned feeds — partial schema coverage detected.{RESET}")
    else:
        print(f"\n{GREEN}All feeds passed schema verification.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
