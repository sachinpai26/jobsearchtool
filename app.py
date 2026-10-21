#!/usr/bin/env python3
"""
Live Job Scanner Web App (Streamlit)
100% PII-Safe: Requires user to upload or paste their config.json.
Queries live career APIs across Greenhouse, Lever, Workday, and SmartRecruiters.
"""

import sys
import json
from pathlib import Path
import pandas as pd
import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
import scan_live_jobs

st.set_page_config(
    page_title="Live Career Portal Job Scanner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎯 Automated Career Portal Live Job Scanner")
st.markdown(
    "Directly queries live corporate job APIs across **Greenhouse, Lever, Workday (CXS), and SmartRecruiters**. "
    "**100% PII-Safe:** No candidate data is saved on the server. Simply upload or paste your `config.json` below."
)

# Sidebar: Config Input
st.sidebar.header("⚙️ Your Search Configuration")

input_method = st.sidebar.radio(
    "How would you like to provide your config?",
    ["📂 Upload config.json", "📝 Paste JSON Content", "📋 Use Sample Template"]
)

active_config = None

if input_method == "📂 Upload config.json":
    uploaded_file = st.sidebar.file_uploader("Upload your config.json file", type=["json"])
    if uploaded_file is not None:
        try:
            active_config = json.load(uploaded_file)
            st.sidebar.success("✅ Config uploaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error parsing JSON: {e}")

elif input_method == "📝 Paste JSON Content":
    pasted_text = st.sidebar.text_area("Paste your config.json text here", height=250)
    if pasted_text.strip():
        try:
            active_config = json.loads(pasted_text)
            st.sidebar.success("✅ JSON parsed successfully!")
        except Exception as e:
            st.sidebar.error(f"Invalid JSON: {e}")

elif input_method == "📋 Use Sample Template":
    template_p = BASE_DIR / "configs" / "template_config.json"
    if template_p.exists():
        with open(template_p, "r", encoding="utf-8") as f:
            active_config = json.load(f)
        st.sidebar.info("Using sample software engineering template.")

# Template download button
template_file = BASE_DIR / "configs" / "template_config.json"
if template_file.exists():
    with open(template_file, "r", encoding="utf-8") as f:
        st.sidebar.download_button(
            label="📥 Download Starter Template JSON",
            data=f.read(),
            file_name="job_search_config_template.json",
            mime="application/json"
        )

# Main Application Body
if active_config:
    candidate_name = active_config.get("candidate", {}).get("name", "User")
    target_roles = active_config.get("candidate", {}).get("target_roles", [])
    include_kw = active_config.get("search_filters", {}).get("include_keywords", [])
    loc_kw = active_config.get("search_filters", {}).get("location_keywords", [])

    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("👤 Search Profile")
        st.markdown(f"**Target Level:** {active_config.get('candidate', {}).get('target_level', 'Not specified')}")
        st.markdown("**Target Roles:**")
        for r in target_roles:
            st.markdown(f"- {r}")

    with col2:
        st.subheader("🔍 Active Filters")
        st.markdown(f"**Keywords ({len(include_kw)}):** `{', '.join(include_kw[:8])}...`")
        st.markdown(f"**Locations:** `{', '.join(loc_kw[:5])}...`")
        
        catalog_p = BASE_DIR / "configs" / "companies.json"
        catalog_boards = {}
        if catalog_p.exists():
            with open(catalog_p, "r", encoding="utf-8") as f:
                catalog_boards = json.load(f).get("job_boards", {})

        boards = active_config.get("job_boards") if active_config.get("job_boards") else catalog_boards
        gh_cnt = len(boards.get("greenhouse", []))
        lev_cnt = len(boards.get("lever", []))
        wd_cnt = len(boards.get("workday", []))
        sr_cnt = len(boards.get("smartrecruiters", []))
        st.markdown(f"**Total Tracked Companies:** `{gh_cnt + lev_cnt + wd_cnt + sr_cnt}` (`{gh_cnt} GH` | `{lev_cnt} Lever` | `{wd_cnt} Workday` | `{sr_cnt} SmartRecruiters`)")

    st.divider()

    if st.button("🚀 Scan Live Career Portals Now", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Temporary config for scanner execution
        tmp_cfg = BASE_DIR / "scripts" / "tmp_ephemeral_config.json"
        with open(tmp_cfg, "w", encoding="utf-8") as f:
            json.dump(active_config, f, indent=2)

        scan_live_jobs.init_config(tmp_cfg)

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

        gh_boards = scan_live_jobs.TARGET_GREENHOUSE_BOARDS
        lev_slugs = scan_live_jobs.TARGET_LEVER_COMPANIES
        wd_comps = scan_live_jobs.TARGET_WORKDAY_COMPANIES
        sr_comps = scan_live_jobs.TARGET_SMARTRECRUITERS_COMPANIES

        total_boards = len(gh_boards) + len(lev_slugs) + len(wd_comps) + len(sr_comps)
        processed = 0
        matches = []

        # 1. Scan Greenhouse
        for comp in gh_boards:
            status_text.text(f"Scanning Greenhouse: {comp['company']}...")
            found = scan_live_jobs.scan_greenhouse(session, comp)
            matches.extend(found)
            processed += 1
            progress_bar.progress(processed / max(total_boards, 1))

        # 2. Scan Lever
        for comp in lev_slugs:
            status_text.text(f"Scanning Lever: {comp['company']}...")
            found = scan_live_jobs.scan_lever(session, comp)
            matches.extend(found)
            processed += 1
            progress_bar.progress(processed / max(total_boards, 1))

        # 3. Scan Workday
        for comp in wd_comps:
            status_text.text(f"Scanning Workday: {comp['company']}...")
            found = scan_live_jobs.scan_workday(session, comp)
            matches.extend(found)
            processed += 1
            progress_bar.progress(processed / max(total_boards, 1))

        # 4. Scan SmartRecruiters
        for comp in sr_comps:
            status_text.text(f"Scanning SmartRecruiters: {comp['company']}...")
            found = scan_live_jobs.scan_smartrecruiters(session, comp)
            matches.extend(found)
            processed += 1
            progress_bar.progress(processed / max(total_boards, 1))

        status_text.success(f"Scan complete! Analyzed {total_boards} company portals.")
        progress_bar.progress(1.0)

        # Cleanup ephemeral file
        if tmp_cfg.exists():
            tmp_cfg.unlink()

        # Display Results
        st.subheader(f"🎯 Matched Live Openings ({len(matches)})")

        if matches:
            df = pd.DataFrame(matches)
            
            # Formatting table
            df_display = df.copy()
            df_display.columns = ["Company", "Role Title", "Location", "Job Link"]

            st.dataframe(
                df_display,
                column_config={
                    "Job Link": st.column_config.LinkColumn("Application URL")
                },
                use_container_width=True,
                hide_index=True
            )

            # Export Buttons
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Matches as CSV",
                data=csv_data,
                file_name=f"job_matches_{candidate_name.replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )

            # Markdown export
            md_lines = [
                f"# 🎯 Active Job Matches ({candidate_name})",
                f"**Total Roles Found:** `{len(matches)}`",
                "",
                "| Company | Role Title | Location | Direct Link |",
                "| :--- | :--- | :--- | :--- |"
            ]
            for m in matches:
                md_lines.append(f"| **{m['company']}** | {m['title']} | {m['location']} | [Apply]({m['url']}) |")

            st.download_button(
                label="📥 Download Matches as Markdown",
                data="\n".join(md_lines),
                file_name=f"LATEST_JOB_MATCHES_{candidate_name.replace(' ', '_').upper()}.md",
                mime="text/markdown"
            )
        else:
            st.warning("No live positions currently matched your keywords and location filters. Try broadening your keywords.")
else:
    st.info("👈 Please upload your `config.json` or paste its text in the sidebar to begin scanning.")
