"""
Kenya Government Tender Tracker
-------------------------------
Problem:    Small businesses miss government tenders because the Public
            Procurement Information Portal (PPIP) is slow to browse and
            there's no quick way to see what's new in your line of work.
Input:      Keywords for your business (e.g. "computer, ICT, printer"),
            a category (Goods / Works / Services / any) and how many days
            back to look.
Processing: Fetches all active tenders from the PPIP API
            (tenders.go.ke/api/active-tenders), keeps only those still open
            that match your keywords, and pulls out the bidding requirements.
Output:     A readable list - newest first - with the procuring entity,
            closing date and days left, tender fee, bid security, how to
            submit, AGPO reservation and links to the tender documents.
            Results are also saved to a JSON file.

Usage:
    python tender_tracker.py

Requirements:
    pip install requests
    (No API key needed - PPIP data is public.)
"""

import json
import re
import sys
from datetime import datetime, timedelta

import requests

BASE_URL = "https://tenders.go.ke"
API_URL = f"{BASE_URL}/api/active-tenders"
PER_PAGE = 100
MAX_PAGES = 20          # safety limit: up to 2,000 tenders
TIMEOUT = 20            # seconds - the portal can be slow
CATEGORIES = {"1": "Goods", "2": "Works", "3": "Services", "": None}
LINE = "=" * 64


class TrackerError(Exception):
    """A problem we can explain to the user in plain English."""


# ---------------------------------------------------------------- input

def get_user_input():
    raw = input("Keywords for your business (comma-separated, blank = all): ").strip()
    keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]

    print("Category:  1) Goods   2) Works   3) Services   [Enter] Any")
    choice = input("Choose: ").strip()
    if choice not in CATEGORIES:
        raise TrackerError(f"'{choice}' isn't an option. Type 1, 2, 3 or just press Enter.")
    category = CATEGORIES[choice]

    days_raw = input("Show tenders posted in the last how many days? [14]: ").strip() or "14"
    if not days_raw.isdigit() or int(days_raw) < 1:
        raise TrackerError(f"'{days_raw}' isn't a valid number of days.")

    return keywords, category, int(days_raw)


# ---------------------------------------------------------------- API

def fetch_page(page):
    params = {"perpage": PER_PAGE, "page": page, "order": "asc"}
    try:
        response = requests.get(API_URL, params=params, timeout=TIMEOUT,
                                headers={"Accept": "application/json"})
    except requests.exceptions.Timeout:
        raise TrackerError("The tenders portal took too long to respond. Try again in a minute.")
    except requests.exceptions.ConnectionError:
        raise TrackerError("Couldn't connect to tenders.go.ke. Check your internet connection.")

    if response.status_code == 429:
        raise TrackerError("The portal is limiting requests. Wait a minute and try again.")
    if response.status_code >= 500:
        raise TrackerError("The tenders portal is having problems right now. Try again later.")
    if response.status_code != 200:
        raise TrackerError(f"The tenders portal returned an error (HTTP {response.status_code}).")

    try:
        data = response.json()
    except ValueError:
        raise TrackerError("The portal sent back something that isn't data. It may be under maintenance.")
    if not isinstance(data, dict) or "data" not in data:
        raise TrackerError("The portal's data format has changed. This tool needs updating.")
    return data


def fetch_all_active_tenders():
    first = fetch_page(1)
    tenders = list(first["data"])
    last_page = min(first.get("last_page") or 1, MAX_PAGES)
    print(f"Found {first.get('total', len(tenders))} active tenders on PPIP. Downloading...")
    for page in range(2, last_page + 1):
        tenders.extend(fetch_page(page)["data"])
    return tenders


# ---------------------------------------------------------------- processing

def parse_date(text):
    if not text:
        return None
    try:
        return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def title_of(obj):
    return (obj or {}).get("title") or ""


def summarise(t):
    """Keep only public tender details. The raw API also includes the posting
    officer's personal data (ID number, phone, emails) - deliberately dropped."""
    pe = t.get("pe") or {}
    docs = [
        {"name": (d.get("type") or {}).get("description") or "Document",
         "url": BASE_URL + d["url"] if d.get("url", "").startswith("/") else d.get("url")}
        for d in t.get("documents") or [] if d.get("url")
    ]
    return {
        "id": t.get("id"),
        "title": (t.get("title") or "").strip(),
        "tender_ref": t.get("tender_ref"),
        "procuring_entity": pe.get("name"),
        "entity_location": pe.get("city"),
        "entity_email": pe.get("email"),
        "category": title_of(t.get("procurement_category")),
        "method": title_of(t.get("procurement_method")),
        "published_at": t.get("published_at"),
        "close_at": t.get("close_at"),
        "venue": t.get("venue"),
        "requirements": {
            "tender_fee_kes": t.get("tender_fee") or 0,
            "bid_security_kes": t.get("bid_security_value"),
            "bid_security_percent": t.get("bid_security_percent"),
            "bid_validity_days": t.get("validity_in_days"),
            "submission": [title_of(m) for m in t.get("submission_methods") or []],
            "agpo_reserved": bool(t.get("is_agpo") or t.get("agpo_groups")),
            "agpo_groups": [title_of(g) or g.get("name") for g in t.get("agpo_groups") or []],
            "addendum_issued": bool(t.get("addendum_added")),
        },
        "documents": docs,
        "ocid": t.get("ocid"),
    }


def matches(t, keywords, category, posted_since, now):
    closes = parse_date(t.get("close_at"))
    posted = parse_date(t.get("published_at"))
    if closes and closes < now:
        return False                       # already closed
    if posted and posted < posted_since:
        return False                       # too old
    if category and title_of(t.get("procurement_category")).lower() != category.lower():
        return False
    if keywords:
        text = f"{t.get('title', '')} {(t.get('pe') or {}).get('name', '')}".lower()
        if not any(re.search(rf"\b{re.escape(k)}", text) for k in keywords):
            return False
    return True


# ---------------------------------------------------------------- output

def money(value):
    return f"KES {value:,.0f}" if value else "None"


def time_left(close, now):
    if not close:
        return "unknown"
    delta = close - now
    if delta < timedelta(days=1):
        return f"{max(int(delta.total_seconds() // 3600), 0)} hours left - URGENT"
    return f"{delta.days} days left"


def print_tender(n, s, now):
    req = s["requirements"]
    close = parse_date(s["close_at"])
    posted = parse_date(s["published_at"])

    print(f"\n[{n}] {s['title']}")
    print(f"    {'Entity:':<15}{s['procuring_entity']}" + (f" ({s['entity_location']})" if s["entity_location"] else ""))
    print(f"    {'Category:':<15}{s['category']}  ·  {s['method']}")
    print(f"    {'Tender no.:':<15}{s['tender_ref']}")
    print(f"    {'Posted:':<15}{posted:%a %d %b %Y}" if posted else f"    {'Posted:':<15}unknown")
    print(f"    {'Closes:':<15}{close:%a %d %b %Y, %I:%M %p}  ({time_left(close, now)})" if close
          else f"    {'Closes:':<15}unknown")
    print("    Requirements:")
    print(f"      - Tender fee:     {money(req['tender_fee_kes'])}")
    if req["bid_security_kes"]:
        print(f"      - Bid security:   {money(req['bid_security_kes'])}")
    elif req["bid_security_percent"]:
        print(f"      - Bid security:   {req['bid_security_percent']}% of bid value")
    else:
        print("      - Bid security:   Not required")
    if req["submission"]:
        print(f"      - Submit by:      {', '.join(req['submission'])}")
    if req["bid_validity_days"]:
        print(f"      - Bid valid for:  {req['bid_validity_days']} days")
    if req["agpo_reserved"]:
        groups = ", ".join(g for g in req["agpo_groups"] if g) or "youth, women, persons with disabilities"
        print(f"      - AGPO reserved:  Yes ({groups})")
    if req["addendum_issued"]:
        print("      - Note:           An addendum was issued - read it before bidding")
    for d in s["documents"]:
        print(f"    {d['name']}: {d['url']}")
    print(f"    {'OCID:':<15}{s['ocid']}  (search this on tenders.go.ke)")


def save_to_file(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {filename}")


# ---------------------------------------------------------------- main

def main():
    print("Kenya Government Tender Tracker")
    print("-------------------------------")
    try:
        keywords, category, days = get_user_input()
        now = datetime.now()
        posted_since = now - timedelta(days=days)

        tenders = fetch_all_active_tenders()
        found = [summarise(t) for t in tenders if matches(t, keywords, category, posted_since, now)]
        found.sort(key=lambda s: s["published_at"] or "", reverse=True)

        label = ", ".join(keywords) if keywords else "all tenders"
        print("\n" + LINE)
        print(f"  {len(found)} open tender(s) for: {label}"
              + (f"  ·  {category}" if category else "") + f"  ·  posted in last {days} days")
        print(LINE)

        if not found:
            print("\nNo matching open tenders right now. Try fewer or broader keywords,")
            print("a different category, or more days.")
            return

        for n, s in enumerate(found, 1):
            print_tender(n, s, now)

        print("\n" + LINE)
        stamp = now.strftime("%Y%m%d_%H%M")
        save_to_file({"searched_at": now.isoformat(timespec="seconds"), "keywords": keywords,
                      "category": category, "days": days, "results": found},
                     f"tenders_{stamp}.json")
    except TrackerError as err:
        print(f"\nSorry: {err}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")


if __name__ == "__main__":
    main()
