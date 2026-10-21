#!/usr/bin/env python3
"""
Configurable Multi-User Live Job Postings Scanner
==================================================
Directly queries public Greenhouse and Lever JSON APIs based on criteria
specified in scripts/job_search_config.json.
Supports 12-hour cadence tracking and exports results to a Markdown digest.
"""

import sys
import json
import time
import re
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "scripts" / "job_search_config.json"
METADATA_FILE = BASE_DIR / "scripts" / "scan_metadata.json"

DEFAULT_CONFIG = {
    "candidate": {
        "name": "Candidate",
        "target_level": "Senior / Staff Individual Contributor",
        "target_roles": ["DevOps Engineer", "Platform Engineer", "SRE"]
    },
    "search_filters": {
        "include_keywords": ["devops", "platform", "infrastructure", "sre", "cloud", "kubernetes"],
        "exclude_title_keywords": ["director", "head of", "manager", "vp", "intern", "graduate"],
        "location_keywords": ["bengaluru", "bangalore", "india", "remote - india"],
        "exclude_location_keywords": ["indiana", "indianapolis"]
    },
    "automation": {
        "cadence_hours": 12.0,
        "output_markdown_file": "LATEST_JOB_MATCHES.md"
    },
    "job_boards": {
        "greenhouse": [],
        "lever": []
    }
}

def load_config(path=None):
    target = path if path else CONFIG_FILE
    if target.exists():
        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f), target
        except Exception as e:
            print(f"[!] Warning: Failed to parse {target.name}: {e}. Using defaults.")
    return DEFAULT_CONFIG, target

def build_regex_pattern(keywords_list):
    if not keywords_list:
        return None
    escaped = [re.escape(k) for k in keywords_list]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

def init_config(custom_path=None):
    global CONFIG, CONFIG_FILE, SEARCH_FILTERS, INCLUDE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS
    global LOCATION_KEYWORDS, EXCLUDE_LOCATION_KEYWORDS, CANDIDATE_NAME, AUTOMATION_CFG
    global DEFAULT_CADENCE, DIGEST_FILE, TARGET_GREENHOUSE_BOARDS, TARGET_LEVER_COMPANIES
    global TARGET_WORKDAY_COMPANIES, TARGET_SMARTRECRUITERS_COMPANIES
    global EXCLUDE_TITLE_REGEX, LOCATION_REGEX

    CONFIG, CONFIG_FILE = load_config(custom_path)
    SEARCH_FILTERS = CONFIG.get("search_filters", DEFAULT_CONFIG["search_filters"])
    INCLUDE_KEYWORDS = [k.lower() for k in SEARCH_FILTERS.get("include_keywords", [])]
    EXCLUDE_TITLE_KEYWORDS = [k.lower() for k in SEARCH_FILTERS.get("exclude_title_keywords", [])]
    LOCATION_KEYWORDS = [k.lower() for k in SEARCH_FILTERS.get("location_keywords", [])]
    EXCLUDE_LOCATION_KEYWORDS = [k.lower() for k in SEARCH_FILTERS.get("exclude_location_keywords", [])]

    CANDIDATE_NAME = CONFIG.get("candidate", {}).get("name", "Candidate")
    AUTOMATION_CFG = CONFIG.get("automation", DEFAULT_CONFIG["automation"])
    DEFAULT_CADENCE = AUTOMATION_CFG.get("cadence_hours", 12.0)
    DIGEST_FILE = BASE_DIR / AUTOMATION_CFG.get("output_markdown_file", "LATEST_JOB_MATCHES.md")

    TARGET_GREENHOUSE_BOARDS = CONFIG.get("job_boards", {}).get("greenhouse", [])
    TARGET_LEVER_COMPANIES = CONFIG.get("job_boards", {}).get("lever", [])
    TARGET_WORKDAY_COMPANIES = CONFIG.get("job_boards", {}).get("workday", [])
    TARGET_SMARTRECRUITERS_COMPANIES = CONFIG.get("job_boards", {}).get("smartrecruiters", [])

    EXCLUDE_TITLE_REGEX = build_regex_pattern(EXCLUDE_TITLE_KEYWORDS)
    LOCATION_REGEX = build_regex_pattern(LOCATION_KEYWORDS)

init_config()

def is_matching_title(title_str):
    if not title_str:
        return False
    t = title_str.lower()
    # Must match at least one inclusion keyword
    if not any(k in t for k in INCLUDE_KEYWORDS):
        return False
    # Must not match any exclusion keyword
    if EXCLUDE_TITLE_REGEX and EXCLUDE_TITLE_REGEX.search(t):
        return False
    return True

def is_matching_location(loc_str):
    if not loc_str:
        return False
    loc = loc_str.lower()
    # Check for excluded locations (e.g., Indiana vs India)
    if any(ex in loc for ex in EXCLUDE_LOCATION_KEYWORDS):
        # Allow only if it legitimately also contains a target location keyword
        if not any(k in loc for k in ["bengaluru", "bangalore"]):
            return False
    if LOCATION_REGEX and LOCATION_REGEX.search(loc):
        return True
    return any(k in loc for k in LOCATION_KEYWORDS)

def scan_greenhouse(session, comp):
    board = comp.get("board", "")
    cname = comp.get("company", board)
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    matches = []
    try:
        r = session.get(url, timeout=12)
        if r.status_code == 200:
            data = r.json()
            jobs = data.get("jobs", [])
            for j in jobs:
                title = j.get("title", "")
                loc = (j.get("location", {}) or {}).get("name", "")

                if is_matching_title(title) and is_matching_location(loc):
                    matches.append({
                        "company": cname,
                        "title": title,
                        "location": loc or "Target Region",
                        "url": j.get("absolute_url", f"https://boards.greenhouse.io/{board}")
                    })
    except Exception:
        pass
    return matches

def scan_lever(session, comp):
    slug = comp.get("slug", "")
    cname = comp.get("company", slug)
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    matches = []
    try:
        r = session.get(url, timeout=12)
        if r.status_code == 200:
            jobs = r.json()
            for j in jobs:
                title = j.get("text", "")
                loc = (j.get("categories", {}) or {}).get("location", "")

                if is_matching_title(title) and is_matching_location(loc):
                    matches.append({
                        "company": cname,
                        "title": title,
                        "location": loc or "Target Region",
                        "url": j.get("hostedUrl", f"https://jobs.lever.co/{slug}")
                    })
    except Exception:
        pass
    return matches

def scan_workday(session, comp):
    tenant = comp.get("tenant", "")
    site = comp.get("site", "")
    dc = comp.get("dc", "wd1")
    cname = comp.get("company", tenant)
    base_url = f"https://{tenant}.{dc}.myworkdayjobs.com"
    endpoint = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"
    
    matches = []
    headers = {
        "Origin": base_url,
        "Referer": f"{base_url}/en-US/{site}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "devops"
    }
    try:
        r = session.post(endpoint, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("jobPostings", []):
                title = j.get("title", "")
                loc = j.get("locationsText", "")
                ext_path = j.get("externalPath", "")
                if is_matching_title(title) and is_matching_location(loc):
                    matches.append({
                        "company": cname,
                        "title": title,
                        "location": loc or "Target Region",
                        "url": f"{base_url}/en-US/{site}{ext_path}"
                    })
    except Exception:
        pass
    return matches

def scan_smartrecruiters(session, comp):
    cid = comp.get("company_id", "")
    cname = comp.get("company", cid)
    url = f"https://api.smartrecruiters.com/v1/companies/{cid}/postings?country=in&limit=100"
    matches = []
    try:
        r = session.get(url, timeout=12)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("content", []):
                title = j.get("name", "")
                city = (j.get("location", {}) or {}).get("city", "")
                jid = j.get("id", "")
                if is_matching_title(title) and is_matching_location(city):
                    matches.append({
                        "company": cname,
                        "title": title,
                        "location": city or "India",
                        "url": f"https://jobs.smartrecruiters.com/{cid}/{jid}"
                    })
    except Exception:
        pass
    return matches


def should_run(cadence_hours):
    if not METADATA_FILE.exists():
        return True
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
            last_epoch = meta.get("last_run_epoch", 0)
            elapsed = time.time() - last_epoch
            if elapsed < (cadence_hours * 3600):
                remaining_mins = int(((cadence_hours * 3600) - elapsed) / 60)
                print(f"[i] Cooldown active: Last run was {elapsed/3600:.1f} hours ago.")
                print(f"[i] Next scan in ~{remaining_mins} minutes (Run with --force to override).")
                return False
    except Exception:
        return True
    return True

def record_run(total_found):
    now_utc = datetime.now(timezone.utc)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist_tz)
    
    meta = {
        "last_run_epoch": time.time(),
        "last_run_ist": now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "total_jobs_found": total_found
    }
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def save_digest(matches, run_time_str):
    loc_summary = ", ".join(LOCATION_KEYWORDS[:3]).title()
    lines = [
        f"# 🎯 Active Job Matches ({CANDIDATE_NAME})",
        f"**Last Automated Scan:** `{run_time_str}` | **Total Roles Identified:** `{len(matches)}`",
        "",
        f"> Filter configuration loaded dynamically from [`scripts/{CONFIG_FILE.name}`](scripts/{CONFIG_FILE.name}).",
        f"> Cadence: Automatically runs every {DEFAULT_CADENCE:.0f} hours from the last run whenever your laptop starts or logs in.",
        "",
        "| # | Company | Role Title | Location | Direct Apply / Job Link |",
        "| :---: | :--- | :--- | :--- | :--- |"
    ]

    for idx, j in enumerate(matches, 1):
        lines.append(f"| {idx} | **{j['company']}** | {j['title']} | {j['location']} | [View & Apply]({j['url']}) |")

    lines.extend([
        "",
        "---",
        f"### 💡 Next Steps for {CANDIDATE_NAME}:",
        "1. Prioritize roles at **DevOps Toolmakers & Tier-1 Platforms** where your tech stack matches production requirements.",
        "2. Cross-reference connections on LinkedIn for warm referrals before direct ATS submission.",
        "3. Update application status in [`Careers Sites.xlsx`](Careers%20Sites.xlsx) when applying."
    ])

    with open(DIGEST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Saved digest to {DIGEST_FILE.name}")

def main():
    parser = argparse.ArgumentParser(description="Configurable live job scanner.")
    parser.add_argument("--force", action="store_true", help="Force run regardless of cadence window.")
    parser.add_argument("--cadence", type=float, default=DEFAULT_CADENCE, help="Cadence in hours.")
    parser.add_argument("--config", type=str, help="Path to alternative JSON config file.")
    args = parser.parse_args()

    if args.config:
        cfg_p = Path(args.config)
        if not cfg_p.is_absolute():
            cfg_p = (BASE_DIR / cfg_p).resolve()
        init_config(cfg_p)

    cadence = args.cadence if args.cadence else DEFAULT_CADENCE

    if not args.force and not should_run(cadence):
        return

    print("=" * 75)
    print(f" Live Role Scanner: {CANDIDATE_NAME}")
    print("=" * 75)
    print(f"Filters loaded from: {CONFIG_FILE.name}")
    print(f"Tracking {len(TARGET_GREENHOUSE_BOARDS)} Greenhouse, {len(TARGET_LEVER_COMPANIES)} Lever, {len(TARGET_WORKDAY_COMPANIES)} Workday, and {len(TARGET_SMARTRECRUITERS_COMPANIES)} SmartRecruiters portals...\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    all_matches = []

    for comp in TARGET_GREENHOUSE_BOARDS:
        found = scan_greenhouse(session, comp)
        if found:
            print(f"[+] {comp['company']} (Greenhouse): Found {len(found)} matching role(s)")
            all_matches.extend(found)

    for comp in TARGET_LEVER_COMPANIES:
        found = scan_lever(session, comp)
        if found:
            print(f"[+] {comp['company']} (Lever): Found {len(found)} matching role(s)")
            all_matches.extend(found)

    for comp in TARGET_WORKDAY_COMPANIES:
        found = scan_workday(session, comp)
        if found:
            print(f"[+] {comp['company']} (Workday): Found {len(found)} matching role(s)")
            all_matches.extend(found)

    for comp in TARGET_SMARTRECRUITERS_COMPANIES:
        found = scan_smartrecruiters(session, comp)
        if found:
            print(f"[+] {comp['company']} (SmartRecruiters): Found {len(found)} matching role(s)")
            all_matches.extend(found)


    ist_tz = timezone(timedelta(hours=5, minutes=30))
    run_time_str = datetime.now(timezone.utc).astimezone(ist_tz).strftime("%Y-%m-%d %I:%M %p IST")

    record_run(len(all_matches))
    save_digest(all_matches, run_time_str)

    print("\n" + "=" * 75)
    print(f" RESULTS: Found {len(all_matches)} relevant openings matching config criteria")
    print("=" * 75)

    if all_matches:
        for idx, job in enumerate(all_matches, 1):
            print(f"\n[{idx}] {job['company']} - {job['title']}")
            print(f"    Location: {job['location']}")
            print(f"    Link:     {job['url']}")
    else:
        print("\nNo immediate openings matching keywords right now. Check back periodically.")

if __name__ == "__main__":
    main()
