# 🎯 Automated Career Portal Live Job Scanner

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated_Scans-green.svg)](https://github.com/sachinpai26/jobsearchtool/actions)
[![Streamlit UI](https://img.shields.io/badge/Streamlit-Interactive_Web_App-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero PII](https://img.shields.io/badge/Privacy-100%25_PII_Safe-brightgreen.svg)](#privacy--pii-safety)

An open-source, serverless multi-ATS job scanner that **directly queries official REST/JSON career APIs** across **Greenhouse, Lever, Workday (CXS), and SmartRecruiters**.

No Selenium, no Puppeteer, no proxy scrapers, and no browser automation needed. It pulls verified live corporate openings in seconds and filters them against your customized role titles and geographic regions.

---

## 🔒 Privacy & PII Safety
**Zero candidate profiles or personal data are stored in this repository.**
Users provide their own JSON configuration when running the scanner (via upload, text paste, or GitHub Actions input). Ephemeral runs process the search in-memory and discard configs immediately after execution.

---

## ⚡ Three Ways to Run It

### 🌐 Method 1: On GitHub Actions (Zero Local Installation)
Anyone can run scans directly inside GitHub's free cloud environment without installing Python:

1. Go to the [**Actions**](https://github.com/sachinpai26/jobsearchtool/actions) tab at the top of this repository.
2. Select **"Live Career Portal Job Scanner"** in the left sidebar.
3. Click the **"Run workflow"** button.
4. **Paste your `config.json` text** directly into the input box (or check *"Run with sample demo template"*).
5. Click **"Run workflow"**.
6. In ~30 seconds, view the results directly on your screen in the **GitHub Step Summary** with verified application links, or download the Markdown report from **Artifacts**!

---

### 🖥️ Method 2: Free Interactive Web App (Streamlit)
Run a full-featured web dashboard locally or deploy it to [Streamlit Community Cloud](https://streamlit.io/cloud) in 1 click:

```bash
pip install -r requirements.txt
streamlit run app.py
```
* **Drag-and-Drop:** Upload your own `config.json` or paste JSON directly in the sidebar.
* **Interactive Table:** View matched openings with live search, filters, and direct application links.
* **1-Click Export:** Download results as `.csv` or `.md`.

---

### 💻 Method 3: Local Command Line
For local execution on Windows/Mac/Linux:

```bash
# 1. Install dependencies
pip install requests urllib3 openpyxl

# 2. Run with your personal JSON config
python scripts/scan_live_jobs.py --config path/to/your_config.json --force
```

---

## 🛠️ How to Customize Your JSON Configuration

Download the starter template from [`configs/template_config.json`](configs/template_config.json) and configure your keywords, locations, and companies:

```json
{
  "candidate": {
    "name": "Candidate",
    "target_level": "Senior / Staff Individual Contributor",
    "target_roles": ["DevOps Engineer", "Platform Engineer", "SRE"]
  },
  "search_filters": {
    "include_keywords": ["devops", "platform", "sre", "cloud", "kubernetes"],
    "exclude_title_keywords": ["director", "head of", "vp", "manager", "intern"],
    "location_keywords": ["bengaluru", "bangalore", "remote - india", "india"],
    "exclude_location_keywords": ["indiana", "indianapolis"]
  },
  "job_boards": {
    "greenhouse": [
      {"company": "Stripe", "board": "stripe"},
      {"company": "GitLab", "board": "gitlab"}
    ],
    "lever": [
      {"company": "Meesho", "slug": "meesho"},
      {"company": "CRED", "slug": "cred"}
    ],
    "workday": [
      {"company": "NVIDIA", "tenant": "nvidia", "dc": "wd5", "site": "NVIDIAExternalCareerSite"},
      {"company": "CrowdStrike", "tenant": "crowdstrike", "dc": "wd5", "site": "crowdstrikecareers"}
    ],
    "smartrecruiters": [
      {"company": "ServiceNow", "company_id": "ServiceNow"},
      {"company": "Renesas Electronics", "company_id": "RenesasElectronics"}
    ]
  }
}
```

### Adding New Companies
* **Greenhouse:** Career URL `boards.greenhouse.io/<board_name>` $\rightarrow$ `{"company": "...", "board": "..."}`
* **Lever:** Career URL `jobs.lever.co/<slug>` $\rightarrow$ `{"company": "...", "slug": "..."}`
* **Workday:** Career URL `<tenant>.<dc>.myworkdayjobs.com/.../<site>` $\rightarrow$ `{"company": "...", "tenant": "...", "dc": "...", "site": "..."}`
* **SmartRecruiters:** Career URL `jobs.smartrecruiters.com/<company_id>` $\rightarrow$ `{"company": "...", "company_id": "..."}`

---

## 📁 Repository Structure

```text
├── .github/
│   └── workflows/
│       └── scan_jobs.yml               # GitHub Actions workflow (ephemeral & PII-safe)
├── configs/
│   └── template_config.json            # Anonymous starter template for users
├── scripts/
│   ├── scan_live_jobs.py               # Core multi-ATS live API query engine
│   ├── enrich_and_verify_careers.py    # Master Excel tracker generator
│   └── README.md                       # Technical scripts guide
├── app.py                              # Streamlit interactive web application
├── Careers Sites.xlsx                  # 190-company verified master employer directory
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Strict PII protection (blocks candidate JSONs/resumes)
└── README.md                           # This guide
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
