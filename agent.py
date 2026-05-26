import streamlit as st
from groq import Groq
import httpx
from bs4 import BeautifulSoup
import json
import re
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import threading

st.set_page_config(
    page_title="Full Auto Job Agent",
    page_icon="🎯",
    layout="wide"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
code, .stCode { font-family: 'JetBrains Mono', monospace !important; }

.stApp { background: #0a0a0f; color: #e8e8f0; }

.metric-card {
    background: linear-gradient(135deg, #12121a, #1a1a28);
    border: 1px solid #2a2a3f;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6c63ff, #ff6584);
}
.metric-val { font-size: 2rem; font-weight: 800; color: #6c63ff; }
.metric-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.2rem; }

.job-card {
    background: #12121a;
    border: 1px solid #2a2a3f;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: #6c63ff; }
.job-card.apply { border-left: 3px solid #00e676; }
.job-card.skip  { border-left: 3px solid #ff5252; }
.job-card.pending { border-left: 3px solid #ffd740; }

.tag {
    display: inline-block;
    background: #1e1e2e;
    border: 1px solid #3a3a5c;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.72rem;
    color: #aaa;
    margin: 2px;
    font-family: 'JetBrains Mono', monospace;
}
.score-apply { color: #00e676; font-weight: 700; }
.score-skip  { color: #ff5252; font-weight: 700; }
.score-pending { color: #ffd740; font-weight: 700; }

.status-bar {
    background: #12121a;
    border: 1px solid #2a2a3f;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #6c63ff;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Career Vault ────────────────────────────────────────────────────────────
VAULT = {
  "personal": {
    "name": "Tirumalarao Kilari",
    "email": "kilaritirumalarao@gmail.com",
    "phone": "346-474-6746",
    "location": "Pflugerville, TX",
    "linkedin": "linkedin.com/in/tirumalaraokilari-803829273",
    "github": "github.com/bizygoodz-web",
    "title": "AI Engineer · Prompt Engineer · RAG Systems Builder"
  },
  "summary": "AI Engineer with hands-on experience designing production-grade agentic systems, multi-stage LLM pipelines, and modular backend architectures. Shipped two live web applications. Experienced in Python, JavaScript, SQL across live non-mocked environments.",
  "skills": {
    "languages": ["Python", "JavaScript", "SQL", "Bash"],
    "llm_ai": ["Anthropic Claude", "OpenAI GPT-4", "Google Gemini", "Groq LLaMA", "Prompt Engineering", "System Prompt Design", "RAG Architecture"],
    "frameworks": ["LangChain", "LangGraph", "FastAPI", "Streamlit", "Uvicorn", "Pydantic", "pytest"],
    "vector_retrieval": ["FAISS", "Sentence-Transformers", "Cosine Similarity", "Chunking Strategies", "Embedding Pipelines"],
    "infrastructure": ["GitHub Actions CI/CD", "Render", "Railway", "REST APIs", "Git", "GitHub Copilot"],
    "libraries": ["PyMuPDF", "pdfplumber", "BeautifulSoup", "httpx", "NumPy", "python-dotenv"],
    "security": ["Prompt injection detection", "Authority escalation prevention", "Hallucination mitigation"]
  },
  "experience": [
    {
      "title": "AI Agent & Prompt Engineer (Contract)",
      "company": "Blue Origin IT Staffing — Client: Austinite Market",
      "dates": "2024 – Present",
      "location": "Austin, TX",
      "bullets": [
        "Designed and deployed a multi-stage AI content pipeline: client brief ingestion → prompt engineering → image generation → iterative refinement → production delivery",
        "Engineered detailed system prompts in Google Gemini to autonomously produce brand-consistent marketing assets",
        "Delivered production-ready assets physically deployed at client storefront — validating real-world AI output quality",
        "Translated complex business requirements into precise AI agent instructions for multi-step task execution"
      ]
    }
  ],
  "projects": [
    {
      "name": "ResumeAI", "url": "resumeai-v2.onrender.com",
      "stack": ["Python", "Streamlit", "Groq", "BeautifulSoup", "Render"],
      "bullets": [
        "Built and deployed full-stack AI web application that reads job posting URLs automatically and tailors resumes",
        "Multi-stage pipeline: URL scraping → skill gap analysis → resume rewriting → cover letter generation",
        "Live deployed on Render with PDF/DOCX parsing and real-time Groq LLaMA API calls"
      ]
    },
    {
      "name": "AI Agent with Web Search", "url": "my-ai-agent-app.onrender.com",
      "stack": ["Python", "Streamlit", "Groq", "DuckDuckGo"],
      "bullets": [
        "Conversational AI agent with real-time web search using tool-use loop",
        "LLM decides whether to search, executes search, feeds results back, generates grounded answer",
        "Full multi-turn conversation memory with live search status indicators"
      ]
    },
    {
      "name": "RAG PDF Chat Agent", "url": "github.com/bizygoodz-web/rag-pdf-chat",
      "stack": ["Python", "FAISS", "Claude", "FastAPI", "pytest"],
      "bullets": [
        "Production-grade RAG agent with modular separation: PDF ingestion, vector indexing, semantic retrieval, LLM response",
        "Persistent session state via FAISS index, prompt injection defenses, authority escalation prevention",
        "FastAPI REST server with /ingest /query /health endpoints; 10 unit tests; GitHub Actions CI/CD; RAGAS eval harness"
      ]
    }
  ],
  "education": [{"degree": "Computer Science", "school": "Lindsey Wilson College", "dates": "2022–2023", "location": "Columbia, KY"}],
  "certifications": [
    "DeepLearning.AI — LangChain & Vector Databases in Production (2025, in progress)",
    "GitHub Copilot — daily use",
    "Claude API (claude-sonnet-4) — system prompts, token management, grounding strategies"
  ],
  "preferences": {
    "available": "Immediately",
    "work_auth": "Yes, authorized to work in the US",
    "salary": "Open to discussion based on full compensation package",
    "remote": True
  }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

TRACKER_FILE = "applications.json"

SYSTEM_PROMPT = f"""You are the Lead Systems Architect and Career Strategist for a Full Auto Premium Job Agent.

CAREER VAULT (USE ONLY THESE FACTS — ZERO HALLUCINATION):
{json.dumps(VAULT, indent=2)}

SCORING WEIGHTS:
- 40% Technical/Hard Skills match
- 30% Role Seniority/Experience match
- 30% Industry Alignment

RULES:
1. NEVER invent skills or facts not in the Career Vault
2. If match score < 80, output ONLY decision SKIP with detailed skip_reason
3. Map Vault language to JD language (dialect alignment)
4. Respond ONLY with valid JSON — no markdown fences, no extra text

OUTPUT FORMAT (strict JSON):
{{
  "decision": "APPLY" or "SKIP",
  "match_score": <0-100>,
  "score_breakdown": {{
    "technical_skills": <0-40>,
    "seniority_experience": <0-30>,
    "industry_alignment": <0-30>
  }},
  "skip_reason": "N/A if applying",
  "matched_keywords": ["kw1", "kw2"],
  "missing_keywords": ["kw1", "kw2"],
  "tailored_bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "cover_letter": "150 word cover letter focused on top 3 reasons for fit",
  "screening_answers": {{
    "Tell me about yourself": "2-3 sentence answer",
    "Why do you want this role": "2-3 sentence answer",
    "What is your greatest strength": "2-3 sentence answer relevant to JD"
  }},
  "sheet_log": "One sentence daily log e.g. Applied: 88% Match - Strong alignment with X"
}}"""

# ── Tracker ─────────────────────────────────────────────────────────────────
def load_tracker() -> list:
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE) as f:
                return json.load(f)
        except:
            return []
    return []

def save_tracker(data: list):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_application(job: dict, result: dict):
    tracker = load_tracker()
    entry = {
        "id": f"{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "title": job.get("title", "Unknown"),
        "company": job.get("company", "Unknown"),
        "url": job.get("url", ""),
        "source": job.get("source", ""),
        "decision": result.get("decision", "SKIP"),
        "match_score": result.get("match_score", 0),
        "score_breakdown": result.get("score_breakdown", {}),
        "skip_reason": result.get("skip_reason", ""),
        "matched_keywords": result.get("matched_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "tailored_bullets": result.get("tailored_bullets", []),
        "cover_letter": result.get("cover_letter", ""),
        "screening_answers": result.get("screening_answers", {}),
        "sheet_log": result.get("sheet_log", ""),
        "status": "ready_to_apply" if result.get("decision") == "APPLY" else "skipped"
    }
    tracker.insert(0, entry)
    save_tracker(tracker)
    return entry

# ── Scrapers ────────────────────────────────────────────────────────────────
def scrape_remoteok(keywords: list[str]) -> list[dict]:
    jobs = []
    try:
        r = httpx.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = r.json()
        kw_lower = [k.lower() for k in keywords]
        for item in data:
            if not isinstance(item, dict) or "position" not in item:
                continue
            title = item.get("position", "")
            desc = item.get("description", "")
            tags = " ".join(item.get("tags", []))
            combined = f"{title} {desc} {tags}".lower()
            if any(k in combined for k in kw_lower):
                jobs.append({
                    "title": title,
                    "company": item.get("company", "Unknown"),
                    "url": item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id','')}"),
                    "description": BeautifulSoup(desc, "html.parser").get_text()[:1500],
                    "source": "RemoteOK",
                    "date": item.get("date", "")
                })
    except Exception as e:
        st.warning(f"RemoteOK scrape error: {e}")
    return jobs[:15]

def scrape_weworkremotely(keywords: list[str]) -> list[dict]:
    jobs = []
    categories = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    ]
    kw_lower = [k.lower() for k in keywords]
    for cat_url in categories:
        try:
            r = httpx.get(cat_url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item")[:20]:
                title = item.find("title").get_text() if item.find("title") else ""
                desc_raw = item.find("description").get_text() if item.find("description") else ""
                desc = BeautifulSoup(desc_raw, "html.parser").get_text()[:1500]
                link = item.find("link").get_text() if item.find("link") else ""
                combined = f"{title} {desc}".lower()
                if any(k in combined for k in kw_lower):
                    company_tag = item.find("region") or item.find("company-name")
                    company = company_tag.get_text() if company_tag else "Unknown"
                    jobs.append({
                        "title": title.replace("&lt;", "").replace("&gt;", "").strip(),
                        "company": company,
                        "url": link,
                        "description": desc,
                        "source": "WeWorkRemotely",
                        "date": ""
                    })
        except Exception as e:
            continue
    return jobs[:15]

def scrape_linkedin_search(keywords: list[str]) -> list[dict]:
    """Scrape LinkedIn job search results page (public, no login needed for search)."""
    jobs = []
    query = "+".join(keywords[:3])
    url = f"https://www.linkedin.com/jobs/search/?keywords={query}&f_AL=true&f_WT=2&sortBy=DD"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_=re.compile("job-search-card|base-card", re.I))[:15]
        for card in cards:
            title_el = card.find(["h3", "h4"], class_=re.compile("title|job-title", re.I))
            company_el = card.find(["h4", "a"], class_=re.compile("company|subtitle", re.I))
            link_el = card.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            link = link_el["href"].split("?")[0] if link_el else ""
            if title:
                jobs.append({
                    "title": title,
                    "company": company,
                    "url": link,
                    "description": f"{title} at {company} — LinkedIn Easy Apply position. Remote.",
                    "source": "LinkedIn",
                    "date": ""
                })
    except Exception as e:
        st.warning(f"LinkedIn scrape warning: {e}")
    return jobs

def fetch_full_job_text(url: str) -> str:
    """Fetch full job description from a job URL."""
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
            tag.decompose()
        signals = ["job-description","jobDescription","description","job-details","responsibilities","qualifications","show-more-less-html"]
        block = None
        for s in signals:
            block = soup.find(id=re.compile(s, re.I)) or soup.find(class_=re.compile(s, re.I))
            if block:
                break
        text = block.get_text("\n", strip=True) if block else soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip() and len(l.strip()) > 2]
        return "\n".join(lines)[:3000]
    except:
        return ""

# ── AI Scorer ───────────────────────────────────────────────────────────────
def run_agent(job_text: str) -> dict:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Evaluate this job and produce the full JSON output:\n\n{job_text[:2500]}"}
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def scrape_single_url(url: str) -> str:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
            tag.decompose()
        signals = ["job-description","jobDescription","description","job-details","responsibilities","qualifications"]
        block = None
        for s in signals:
            block = soup.find(id=re.compile(s, re.I)) or soup.find(class_=re.compile(s, re.I))
            if block:
                break
        text = block.get_text("\n", strip=True) if block else soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip() and len(l.strip()) > 2]
        return "\n".join(lines)[:4000]
    except Exception as e:
        raise ValueError(f"Could not fetch job page: {e}")

# ── Email Digest ─────────────────────────────────────────────────────────────
def send_email_digest(tracker: list, smtp_user: str, smtp_pass: str, to_email: str):
    today = date.today().isoformat()
    today_jobs = [j for j in tracker if j.get("date") == today]
    applies = [j for j in today_jobs if j.get("decision") == "APPLY"]
    skips = [j for j in today_jobs if j.get("decision") == "SKIP"]

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#0a0a0f;color:#e8e8f0;padding:2rem;">
    <h2 style="color:#6c63ff;">🎯 Full Auto Job Agent — Daily Digest</h2>
    <p style="color:#aaa;">{today} · {len(today_jobs)} jobs evaluated · {len(applies)} matches</p>
    <hr style="border-color:#2a2a3f;">
    <h3 style="color:#00e676;">✅ APPLY ({len(applies)} matches)</h3>
    {''.join(f"""
    <div style="background:#12121a;border-left:3px solid #00e676;border-radius:8px;padding:1rem;margin-bottom:1rem;">
      <strong style="color:#fff;">{j['title']}</strong> @ {j['company']}<br>
      <span style="color:#6c63ff;font-weight:700;">{j['match_score']}% match</span>
      <span style="color:#aaa;font-size:0.85em;margin-left:1rem;">{j['source']}</span><br>
      <a href="{j['url']}" style="color:#6c63ff;">Open Application →</a><br>
      <em style="color:#888;font-size:0.85em;">{j.get('sheet_log','')}</em>
    </div>
    """ for j in applies) if applies else "<p style='color:#888;'>No matches today.</p>"}
    <h3 style="color:#ff5252;">❌ SKIPPED ({len(skips)} jobs)</h3>
    {''.join(f"<p style='color:#888;font-size:0.85em;'>• {j['title']} @ {j['company']} — {j.get('skip_reason','Score too low')[:80]}</p>" for j in skips[:5]) if skips else ""}
    <hr style="border-color:#2a2a3f;">
    <p style="color:#555;font-size:0.75em;">Full Auto Job Agent v3 · {VAULT['personal']['name']}</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 Job Agent Digest: {len(applies)} matches today ({today})"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())

# ── Session state ────────────────────────────────────────────────────────────
if "scan_log" not in st.session_state:
    st.session_state.scan_log = []
if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:1.5rem 0 0.5rem;">
  <h1 style="font-family:'Syne',sans-serif;font-weight:800;font-size:2.2rem;margin:0;
             background:linear-gradient(90deg,#6c63ff,#ff6584);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    🎯 Full Auto Job Agent
  </h1>
  <p style="color:#666;font-family:'JetBrains Mono',monospace;font-size:0.8rem;margin:0.3rem 0 0;">
    {VAULT['personal']['name']} · {VAULT['personal']['location']} · 80% Gate · llama-3.3-70b
  </p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🤖 Auto Hunt", "🔍 Single Job", "📊 Tracker", "⚙️ Settings"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: AUTO HUNT
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Autonomous Job Hunt")
    st.caption("Pulls live jobs from RemoteOK + WeWorkRemotely + LinkedIn, scores each one, logs results")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        keywords_input = st.text_input(
            "Search keywords (comma-separated)",
            value="AI Engineer, Prompt Engineer, LLM, RAG, Python",
            help="What roles to search for"
        )
    with col_cfg2:
        sources = st.multiselect(
            "Job boards to scan",
            ["RemoteOK", "WeWorkRemotely", "LinkedIn"],
            default=["RemoteOK", "WeWorkRemotely", "LinkedIn"]
        )

    col_s1, col_s2, col_s3 = st.columns(3)
    tracker_data = load_tracker()
    applies_total = sum(1 for j in tracker_data if j.get("decision") == "APPLY")
    skips_total = sum(1 for j in tracker_data if j.get("decision") == "SKIP")

    with col_s1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{len(tracker_data)}</div><div class="metric-label">Total Evaluated</div></div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#00e676">{applies_total}</div><div class="metric-label">Ready to Apply</div></div>', unsafe_allow_html=True)
    with col_s3:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#ff5252">{skips_total}</div><div class="metric-label">Skipped</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Start Auto Hunt", use_container_width=True, type="primary", disabled=st.session_state.is_scanning):
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        st.session_state.is_scanning = True
        st.session_state.scan_log = []

        log_box = st.empty()
        progress = st.progress(0)
        results_box = st.container()

        # Scrape phase
        all_jobs = []
        log_box.markdown('<div class="status-bar">⚡ Scraping job boards...</div>', unsafe_allow_html=True)

        if "RemoteOK" in sources:
            rjobs = scrape_remoteok(keywords)
            all_jobs.extend(rjobs)
            st.session_state.scan_log.append(f"RemoteOK: {len(rjobs)} jobs found")

        if "WeWorkRemotely" in sources:
            wjobs = scrape_weworkremotely(keywords)
            all_jobs.extend(wjobs)
            st.session_state.scan_log.append(f"WeWorkRemotely: {len(wjobs)} jobs found")

        if "LinkedIn" in sources:
            ljobs = scrape_linkedin_search(keywords)
            all_jobs.extend(ljobs)
            st.session_state.scan_log.append(f"LinkedIn: {len(ljobs)} jobs found")

        # Deduplicate by URL
        seen = set()
        unique_jobs = []
        for j in all_jobs:
            key = j.get("url", j.get("title",""))
            if key and key not in seen:
                seen.add(key)
                unique_jobs.append(j)

        st.session_state.scan_log.append(f"Total unique jobs: {len(unique_jobs)}")

        if not unique_jobs:
            st.warning("No jobs found. Try different keywords or check your internet connection.")
            st.session_state.is_scanning = False
        else:
            # Score each job
            apply_count = 0
            skip_count = 0

            for i, job in enumerate(unique_jobs):
                pct = int((i / len(unique_jobs)) * 100)
                progress.progress(pct)
                log_box.markdown(
                    f'<div class="status-bar">🔍 [{i+1}/{len(unique_jobs)}] Scoring: {job["title"][:50]} @ {job["company"][:30]}...</div>',
                    unsafe_allow_html=True
                )

                # Get full description if we have a URL
                job_text = job.get("description", "")
                if job.get("url") and len(job_text) < 300:
                    full = fetch_full_job_text(job["url"])
                    if full:
                        job_text = full

                if not job_text.strip():
                    st.session_state.scan_log.append(f"⚠ Skipped (no content): {job['title']}")
                    continue

                try:
                    result = run_agent(job_text)
                    entry = log_application(job, result)
                    decision = result.get("decision", "SKIP")
                    score = result.get("match_score", 0)

                    if decision == "APPLY":
                        apply_count += 1
                        st.session_state.scan_log.append(f"✅ APPLY {score}% — {job['title']} @ {job['company']}")
                        with results_box:
                            st.success(f"✅ **{score}%** — {job['title']} at **{job['company']}** ({job['source']})  \n[Open job →]({job['url']})")
                    else:
                        skip_count += 1
                        st.session_state.scan_log.append(f"❌ SKIP {score}% — {job['title']} @ {job['company']}")

                    time.sleep(0.5)  # Rate limit
                except json.JSONDecodeError:
                    st.session_state.scan_log.append(f"⚠ JSON error on: {job['title']}")
                except Exception as e:
                    st.session_state.scan_log.append(f"⚠ Error on {job['title']}: {str(e)[:50]}")

            progress.progress(100)
            log_box.markdown(
                f'<div class="status-bar">✅ Done — {apply_count} matches, {skip_count} skipped out of {len(unique_jobs)} jobs</div>',
                unsafe_allow_html=True
            )
            st.session_state.is_scanning = False
            st.balloons()

    # Show scan log
    if st.session_state.scan_log:
        with st.expander("📋 Scan log", expanded=False):
            for line in st.session_state.scan_log:
                st.text(line)

# ═══════════════════════════════════════════════════════════════════
# TAB 2: SINGLE JOB
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Single Job Evaluator")
    col1, col2 = st.columns([2, 1])

    with col1:
        input_method = st.radio("Input method:", ["Paste URL", "Paste job description"], horizontal=True)
        job_text_manual = None
        job_url_manual = ""

        if input_method == "Paste URL":
            job_url_manual = st.text_input("Job posting URL", placeholder="https://boards.greenhouse.io/company/jobs/12345")
            if job_url_manual:
                with st.spinner("Reading job page..."):
                    try:
                        job_text_manual = scrape_single_url(job_url_manual)
                        st.success(f"✓ {len(job_text_manual):,} chars read")
                        with st.expander("Preview"):
                            st.text(job_text_manual[:400] + "...")
                    except Exception as e:
                        st.error(str(e))
        else:
            job_text_manual = st.text_area("Paste full job description", height=250)

    with col2:
        st.subheader("Career Vault")
        st.success(f"✓ {VAULT['personal']['name']}")
        st.caption(f"📍 {VAULT['personal']['location']}")
        st.caption(f"🔧 {len(VAULT['skills']['llm_ai'])} LLM skills")
        st.caption(f"🚀 {len(VAULT['projects'])} live projects")
        st.info("80% gate active")

    if st.button("🎯 Evaluate Job", use_container_width=True, type="primary"):
        if not job_text_manual:
            st.error("Please provide a URL or job description.")
        else:
            with st.spinner("Scoring..."):
                try:
                    result = run_agent(job_text_manual)
                    score = result.get("match_score", 0)
                    decision = result.get("decision", "SKIP")
                    breakdown = result.get("score_breakdown", {})

                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Match Score", f"{score}%")
                    col_b.metric("Decision", decision)
                    col_c.metric("Technical", f"{breakdown.get('technical_skills',0)}/40")
                    col_d.metric("Seniority", f"{breakdown.get('seniority_experience',0)}/30")

                    # Log it
                    job_meta = {
                        "title": "Manual Entry",
                        "company": "Unknown",
                        "url": job_url_manual,
                        "source": "Manual"
                    }
                    log_application(job_meta, result)

                    if decision == "SKIP":
                        st.error("❌ SKIPPED")
                        st.warning(result.get("skip_reason", "Score too low"))
                        st.info("Missing: " + ", ".join(result.get("missing_keywords", [])))
                    else:
                        st.success(f"✅ APPLYING — {score}% match!")
                        st.markdown("**Matched:** " + " ".join([f"`{k}`" for k in result.get("matched_keywords", [])]))

                        with st.expander("📝 Tailored bullets", expanded=True):
                            for b in result.get("tailored_bullets", []):
                                st.markdown(f"• {b}")

                        with st.expander("✉️ Cover letter", expanded=True):
                            st.text_area("", result.get("cover_letter", ""), height=180, label_visibility="collapsed")

                        with st.expander("💬 Screening answers"):
                            for q, a in result.get("screening_answers", {}).items():
                                st.markdown(f"**{q}**")
                                st.code(a, language=None)

                        if job_url_manual:
                            st.link_button("🔗 Open application →", job_url_manual, use_container_width=True, type="primary")

                        package = f"""FULL AUTO JOB AGENT — APPLICATION PACKAGE
{'='*50}
CANDIDATE: {VAULT['personal']['name']}
JOB URL: {job_url_manual or 'Manual input'}
MATCH SCORE: {score}%
DECISION: {decision}

SCORE BREAKDOWN:
Technical Skills: {breakdown.get('technical_skills',0)}/40
Seniority/Experience: {breakdown.get('seniority_experience',0)}/30
Industry Alignment: {breakdown.get('industry_alignment',0)}/30

MATCHED KEYWORDS: {', '.join(result.get('matched_keywords', []))}

TAILORED BULLETS:
{chr(10).join('• ' + b for b in result.get('tailored_bullets', []))}

COVER LETTER:
{result.get('cover_letter','')}

SCREENING ANSWERS:
{chr(10).join(f"Q: {q}{chr(10)}A: {a}{chr(10)}" for q,a in result.get('screening_answers',{}).items())}

YOUR INFO:
Name: {VAULT['personal']['name']}
Email: {VAULT['personal']['email']}
Phone: {VAULT['personal']['phone']}
LinkedIn: {VAULT['personal']['linkedin']}
Available: {VAULT['preferences']['available']}
Work Auth: {VAULT['preferences']['work_auth']}"""

                        st.download_button("⬇ Download package", package,
                            file_name=f"application_{score}pct.txt", mime="text/plain", use_container_width=True)

                except json.JSONDecodeError:
                    st.error("Agent returned invalid JSON. Try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════
# TAB 3: TRACKER DASHBOARD
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Application Tracker")

    tracker_data = load_tracker()

    if not tracker_data:
        st.info("No applications tracked yet. Run Auto Hunt to start.")
    else:
        # Stats row
        applies = [j for j in tracker_data if j.get("decision") == "APPLY"]
        skips = [j for j in tracker_data if j.get("decision") == "SKIP"]
        avg_score = sum(j.get("match_score",0) for j in tracker_data) // max(len(tracker_data),1)
        today_count = sum(1 for j in tracker_data if j.get("date") == date.today().isoformat())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Evaluated", len(tracker_data))
        c2.metric("Matches (80%+)", len(applies))
        c3.metric("Avg Score", f"{avg_score}%")
        c4.metric("Today", today_count)

        st.markdown("---")

        # Filter
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_decision = st.selectbox("Filter by decision", ["All", "APPLY", "SKIP"])
        with filter_col2:
            filter_source = st.selectbox("Filter by source", ["All"] + list(set(j.get("source","") for j in tracker_data)))

        filtered = tracker_data
        if filter_decision != "All":
            filtered = [j for j in filtered if j.get("decision") == filter_decision]
        if filter_source != "All":
            filtered = [j for j in filtered if j.get("source") == filter_source]

        st.caption(f"Showing {len(filtered)} of {len(tracker_data)} entries")

        # Job cards
        for job in filtered[:50]:
            decision = job.get("decision", "SKIP")
            score = job.get("match_score", 0)
            css_class = "apply" if decision == "APPLY" else "skip"
            score_class = "score-apply" if decision == "APPLY" else "score-skip"

            with st.expander(
                f"{'✅' if decision == 'APPLY' else '❌'} {score}% — {job['title']} @ {job['company']} [{job.get('source','')}]",
                expanded=False
            ):
                col_i1, col_i2 = st.columns([3,1])
                with col_i1:
                    st.caption(f"📅 {job.get('timestamp','')[:19]}  |  🌐 {job.get('source','')}  |  🔗 {job.get('url','')[:60]}")
                    if decision == "APPLY":
                        st.markdown("**Matched keywords:** " + " ".join([f"`{k}`" for k in job.get("matched_keywords", [])[:8]]))
                        if job.get("tailored_bullets"):
                            st.markdown("**Top bullet:** " + job["tailored_bullets"][0])
                        if job.get("url"):
                            st.link_button("Open Application →", job["url"])
                    else:
                        st.warning(f"Skip reason: {job.get('skip_reason','')}")
                        st.caption("Missing: " + ", ".join(job.get("missing_keywords", [])[:5]))
                with col_i2:
                    bd = job.get("score_breakdown", {})
                    st.metric("Technical", f"{bd.get('technical_skills',0)}/40")
                    st.metric("Seniority", f"{bd.get('seniority_experience',0)}/30")
                    st.metric("Industry", f"{bd.get('industry_alignment',0)}/30")

        # Export
        if st.button("⬇ Export tracker as JSON", use_container_width=True):
            st.download_button(
                "Download applications.json",
                data=json.dumps(tracker_data, indent=2),
                file_name=f"applications_{date.today().isoformat()}.json",
                mime="application/json"
            )

# ═══════════════════════════════════════════════════════════════════
# TAB 4: SETTINGS
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Settings & Email Digest")

    st.markdown("#### 📧 Email Digest")
    st.caption("Sends a daily summary of all matched jobs to your inbox via Gmail SMTP")

    with st.form("email_form"):
        smtp_user = st.text_input("Your Gmail address (sender)", placeholder="youremail@gmail.com")
        smtp_pass = st.text_input("Gmail App Password", type="password",
            help="Generate at myaccount.google.com/apppasswords — NOT your regular Gmail password")
        to_email = st.text_input("Send digest to", value=VAULT["personal"]["email"])
        send_btn = st.form_submit_button("📨 Send Today's Digest Now", use_container_width=True)

    if send_btn:
        if not smtp_user or not smtp_pass:
            st.error("Enter your Gmail address and App Password.")
        else:
            with st.spinner("Sending..."):
                try:
                    tracker_for_email = load_tracker()
                    send_email_digest(tracker_for_email, smtp_user, smtp_pass, to_email)
                    st.success(f"✅ Digest sent to {to_email}")
                except Exception as e:
                    st.error(f"Email failed: {e}")

    st.markdown("---")
    st.markdown("#### ℹ️ How to set up Gmail App Password")
    st.markdown("""
    1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
    2. Create a new app password → name it "Job Agent"
    3. Copy the 16-character password and paste it above
    4. On Render, add `GROQ_API_KEY` as an environment variable
    """)

    st.markdown("---")
    st.markdown("#### 🗑️ Clear Tracker")
    if st.button("Clear all tracked applications", type="secondary"):
        save_tracker([])
        st.success("Tracker cleared.")
        st.rerun()

    st.markdown("---")
    st.caption(f"Full Auto Job Agent v3 · {VAULT['personal']['name']} · llama-3.3-70b-versatile · 80% Gate")
