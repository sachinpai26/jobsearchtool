# Job Search Automation Scripts Guide

This directory contains standalone, modular Python automation tools designed for tech job searches. 

All search parameters, role keywords, exclusions, locations, and company job boards are **decoupled into central JSON configuration files**, making these scripts reusable for any candidate:
- **Sachin Satish Pai** (`job_search_config.json`): DevOps, Platform, SRE, Cloud Infrastructure
- **Jigyasha Agarwal** (`job_search_config_jigyasha.json`): Full Stack, .NET, Angular, Backend
- **Ganesh Bhandarkar** (`job_search_config_ganesh.json`): Gaming QA Lead, Game Tester, Console & Mobile QA
- **Panchami Mallya** (`job_search_config_panchami.json`): Audit, Assurance, US GAAP, Finance & Accounting

---

## 📋 Table of Contents
1. [Prerequisites & Environment Setup](#1-prerequisites--environment-setup)
2. [Configuration: `job_search_config.json`](#2-configuration-job_search_configjson)
3. [Script 1: `scan_live_jobs.py` (Live API Scanner)](#3-script-1-scan_live_jobspy-live-api-scanner)
4. [Script 2: `enrich_and_verify_careers.py` (Master Excel Tracker)](#4-script-2-enrich_and_verify_careerspy-master-excel-tracker)
5. [Script 3: `build_pdf.py` (Resume Compiler)](#5-script-3-build_pdfpy-resume-compiler)
6. [Automated 12-Hour Cadence Schedule](#6-automated-12-hour-cadence-schedule)

---

## 1. Prerequisites & Environment Setup

These scripts run on Python 3.10+ (Python 3.12 installed on this workstation).

### Default Python Path on this Machine:
```powershell
$PYTHON = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
```

### Install Required Dependencies:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install openpyxl requests urllib3
```

---

## 2. Configuration: `job_search_config.json`

Anyone can customize the search by editing [`scripts/job_search_config.json`](job_search_config.json). No Python coding required!

### Configuration Schema:
```json
{
  "candidate": {
    "name": "Candidate Name",
    "target_level": "Senior / Staff Individual Contributor (IC)",
    "target_roles": ["DevOps Engineer", "Platform Engineer", "SRE"]
  },
  "search_filters": {
    "include_keywords": [
      "devops", "platform", "infrastructure", "site reliability", "sre", "cloud", "kubernetes", "helm", "architect"
    ],
    "exclude_title_keywords": [
      "director", "head of", "vice president", "vp", "manager", "product manager", "sales", "recruiting", "intern"
    ],
    "location_keywords": [
      "bengaluru", "bangalore", "india", "remote - india"
    ],
    "exclude_location_keywords": [
      "indiana", "indianapolis"
    ]
  },
  "automation": {
    "cadence_hours": 12.0,
    "output_markdown_file": "LATEST_JOB_MATCHES.md"
  },
  "job_boards": {
    "greenhouse": [
      {"company": "GitLab", "board": "gitlab"},
      {"company": "Stripe", "board": "stripe"},
      {"company": "Okta", "board": "okta"}
    ],
    "lever": [
      {"company": "Zepto", "slug": "zepto"},
      {"company": "Atlassian", "slug": "atlassian"}
    ],
    "workday": [
      {"company": "CrowdStrike", "tenant": "crowdstrike", "dc": "wd5", "site": "crowdstrikecareers"},
      {"company": "Cisco", "tenant": "cisco", "dc": "wd5", "site": "Cisco_Careers"}
    ],
    "smartrecruiters": [
      {"company": "ServiceNow", "company_id": "ServiceNow"}
    ]
  }
}
```

---

## 3. Script 1: `scan_live_jobs.py` (Live API Scanner)

### What It Does:
* Dynamically loads `job_search_config.json` and queries public REST/JSON APIs across **Greenhouse**, **Lever**, **Workday (CXS)**, and **SmartRecruiters** (ServiceNow).
* Requires **zero browser automation, Selenium, or proxies**.
* Automatically filters titles and locations based on your inclusion and exclusion lists.
* **12-Hour Cadence Gate:** Checks `scripts/scan_metadata.json`. If less than 12 hours have elapsed since the last run, it exits cleanly.
* Generates [`LATEST_JOB_MATCHES.md`](../LATEST_JOB_MATCHES.md) with active openings and direct application links.

### How to Run:
```powershell
# 1. Sachin (DevOps / Platform / SRE / Cloud Lead)
python "scripts\scan_live_jobs.py" --force

# 2. Jigyasha (.NET / Angular / Full Stack Engineer)
python "scripts\scan_live_jobs.py" --config "scripts\job_search_config_jigyasha.json" --force

# 3. Ganesh (Gaming QA Lead / Game Tester / Console & Mobile QA)
python "scripts\scan_live_jobs.py" --config "scripts\job_search_config_ganesh.json" --force

# 4. Panchami (Audit / Assurance / US GAAP / Finance & Accounting)
python "scripts\scan_live_jobs.py" --config "scripts\job_search_config_panchami.json" --force
```

---

## 4. Script 2: `enrich_and_verify_careers.py` (Master Excel Tracker)

### What It Does:
* Pings and checks health across **147 employers** concurrently.
* Categorizes ATS types (**Workday**, **Greenhouse**, **Lever**, **SmartRecruiters**, **Eightfold AI**, **Phenom**, etc.).
* Writes [`Careers Sites.xlsx`](../Careers%20Sites.xlsx) with application status dropdowns, automated search URLs, and dashboard metrics.

### How to Run:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" "scripts\enrich_and_verify_careers.py"
```

---

## 5. Script 3: `build_pdf.py` (Resume Compiler)

### What It Does:
* Uses Chrome headless to render `Sachin_Satish_Pai_Resume.html` into a pixel-perfect, ATS-compliant `Sachin_Satish_Pai_Resume.pdf`.
* Automatically stages to local temporary storage before copying to avoid OneDrive file-locking conflicts.

### How to Run:
```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" "scripts\build_pdf.py"
```

---

## 6. Automated 12-Hour Cadence Schedule

* **Windows Startup Launcher:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SachinJobSearchScanner.vbs` runs silently on every boot/login.
* If $\ge 12\text{ hours}$ have passed since the previous scan, it refreshes `LATEST_JOB_MATCHES.md` in the background.
