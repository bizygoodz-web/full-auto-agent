import streamlit as st
from groq import Groq
import httpx
from bs4 import BeautifulSoup
import json
import re
import os
import time
import smtplib
import threading
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Full Auto Job Agent", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
.metric-card {
    background: linear-gradient(135deg,#12121a,#1a1a28);
    border:1px solid #2a2a3f; border-radius:12px;
    padding:1.2rem 1.5rem; text-align:center; position:relative; overflow:hidden;
}
.metric-card::before { content:''; position:absolute; top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#6c63ff,#ff6584); }
.metric-val { font-size:2rem; font-weight:800; color:#6c63ff; }
.metric-label { font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.2rem; }
.status-bar { background:#12121a; border:1px solid #2a2a3f; border-radius:8px;
    padding:0.6rem 1rem; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#6c63ff; margin-bottom:1rem; }
.sched-active { background:#0d2b1a; border:1px solid #00e676; border-radius:8px;
    padding:0.6rem 1rem; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#00e676; margin-bottom:1rem; }
</style>
""", unsafe_allow_html=True)

# ── Career Vault ─────────────────────────────────────────────────────────────
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
      "dates": "2024 – Present", "location": "Austin, TX",
      "bullets": [
        "Designed and deployed a multi-stage AI content pipeline: client brief ingestion → prompt engineering → image generation → iterative refinement → production delivery",
        "Engineered detailed system prompts in Google Gemini to autonomously produce brand-consistent marketing assets",
        "Delivered production-ready assets physically deployed at client storefront — validating real-world AI output quality",
        "Translated complex business requirements into precise AI agent instructions for multi-step task execution"
      ]
    }
  ],
  "projects": [
    {"name":"ResumeAI","url":"resumeai-v2.onrender.com","stack":["Python","Streamlit","Groq","BeautifulSoup","Render"],
     "bullets":["Built and deployed full-stack AI web application that reads job posting URLs automatically and tailors resumes",
                "Multi-stage pipeline: URL scraping → skill gap analysis → resume rewriting → cover letter generation",
                "Live deployed on Render with PDF/DOCX parsing and real-time Groq LLaMA API calls"]},
    {"name":"AI Agent with Web Search","url":"my-ai-agent-app.onrender.com","stack":["Python","Streamlit","Groq","DuckDuckGo"],
     "bullets":["Conversational AI agent with real-time web search using tool-use loop",
                "LLM decides whether to search, executes search, feeds results back, generates grounded answer",
                "Full multi-turn conversation memory with live search status indicators"]},
    {"name":"RAG PDF Chat Agent","url":"github.com/bizygoodz-web/rag-pdf-chat","stack":["Python","FAISS","Claude","FastAPI","pytest"],
     "bullets":["Production-grade RAG agent with modular separation: PDF ingestion, vector indexing, semantic retrieval, LLM response",
                "Persistent session state via FAISS index, prompt injection defenses, authority escalation prevention",
                "FastAPI REST server with /ingest /query /health endpoints; 10 unit tests; GitHub Actions CI/CD; RAGAS eval harness"]}
  ],
  "education": [{"degree":"Computer Science","school":"Lindsey Wilson College","dates":"2022–2023","location":"Columbia, KY"}],
  "certifications": [
    "DeepLearning.AI — LangChain & Vector Databases in Production (2025, in progress)",
    "GitHub Copilot — daily use",
    "Claude API (claude-sonnet-4) — system prompts, token management, grounding strategies"
  ],
  "preferences": {"available":"Immediately","work_auth":"Yes, authorized to work in the US",
                  "salary":"Open to discussion based on full compensation package","remote":True}
}

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36","Accept-Language":"en-US,en;q=0.9"}
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
  "score_breakdown": {{"technical_skills":<0-40>,"seniority_experience":<0-30>,"industry_alignment":<0-30>}},
  "skip_reason": "N/A if applying",
  "matched_keywords": ["kw1","kw2"],
  "missing_keywords": ["kw1","kw2"],
  "tailored_bullets": ["bullet 1","bullet 2","bullet 3","bullet 4","bullet 5"],
  "cover_letter": "150 word cover letter focused on top 3 reasons for fit",
  "screening_answers": {{
    "Tell me about yourself": "2-3 sentence answer",
    "Why do you want this role": "2-3 sentence answer",
    "What is your greatest strength": "2-3 sentence answer relevant to JD"
  }},
  "sheet_log": "One sentence daily log e.g. Applied: 88% Match - Strong alignment with X"
}}"""

# ── Tracker ───────────────────────────────────────────────────────────────────
def load_tracker() -> list:
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE) as f: return json.load(f)
        except: return []
    return []

def save_tracker(data: list):
    with open(TRACKER_FILE, "w") as f: json.dump(data, f, indent=2)

def already_tracked(url: str) -> bool:
    tracker = load_tracker()
    return any(j.get("url") == url for j in tracker if url)

def log_application(job: dict, result: dict):
    tracker = load_tracker()
    entry = {
        "id": str(int(time.time())),
        "timestamp": datetime.now().isoformat(),
        "date": date.today().isoformat(),
        "title": job.get("title","Unknown"),
        "company": job.get("company","Unknown"),
        "url": job.get("url",""),
        "source": job.get("source",""),
        "decision": result.get("decision","SKIP"),
        "match_score": result.get("match_score",0),
        "score_breakdown": result.get("score_breakdown",{}),
        "skip_reason": result.get("skip_reason",""),
        "matched_keywords": result.get("matched_keywords",[]),
        "missing_keywords": result.get("missing_keywords",[]),
        "tailored_bullets": result.get("tailored_bullets",[]),
        "cover_letter": result.get("cover_letter",""),
        "screening_answers": result.get("screening_answers",{}),
        "sheet_log": result.get("sheet_log",""),
        "status": "ready_to_apply" if result.get("decision")=="APPLY" else "skipped"
    }
    tracker.insert(0, entry)
    save_tracker(tracker)
    return entry

# ── Scrapers ──────────────────────────────────────────────────────────────────
def scrape_remoteok(keywords):
    jobs = []
    try:
        r = httpx.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = r.json()
        kw_lower = [k.lower() for k in keywords]
        for item in data:
            if not isinstance(item,dict) or "position" not in item: continue
            title = item.get("position","")
            desc = BeautifulSoup(item.get("description",""),"html.parser").get_text()[:1500]
            tags = " ".join(item.get("tags",[]))
            if any(k in f"{title} {desc} {tags}".lower() for k in kw_lower):
                jobs.append({"title":title,"company":item.get("company","Unknown"),
                    "url":item.get("url",f"https://remoteok.com/remote-jobs/{item.get('id','')}"),
                    "description":desc,"source":"RemoteOK","date":item.get("date","")})
    except Exception as e:
        st.warning(f"RemoteOK: {e}")
    return jobs[:15]

def scrape_weworkremotely(keywords):
    jobs = []
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    ]
    kw_lower = [k.lower() for k in keywords]
    for url in feeds:
        try:
            r = httpx.get(url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item")[:20]:
                title = item.find("title").get_text() if item.find("title") else ""
                desc = BeautifulSoup(item.find("description").get_text() if item.find("description") else "","html.parser").get_text()[:1500]
                link = item.find("link").get_text() if item.find("link") else ""
                if any(k in f"{title} {desc}".lower() for k in kw_lower):
                    jobs.append({"title":title.strip(),"company":"Unknown","url":link,"description":desc,"source":"WeWorkRemotely","date":""})
        except: continue
    return jobs[:15]

def scrape_linkedin(keywords):
    jobs = []
    query = "+".join(keywords[:3])
    url = f"https://www.linkedin.com/jobs/search/?keywords={query}&f_AL=true&f_WT=2&sortBy=DD"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_=re.compile("job-search-card|base-card",re.I))[:15]
        for card in cards:
            title_el = card.find(["h3","h4"], class_=re.compile("title|job-title",re.I))
            company_el = card.find(["h4","a"], class_=re.compile("company|subtitle",re.I))
            link_el = card.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            link = link_el["href"].split("?")[0] if link_el else ""
            if title:
                jobs.append({"title":title,"company":company,"url":link,
                    "description":f"{title} at {company} — LinkedIn Easy Apply. Remote.","source":"LinkedIn","date":""})
    except Exception as e:
        st.warning(f"LinkedIn: {e}")
    return jobs

def scrape_ycombinator(keywords):
    """Scrape YCombinator Who's Hiring thread from Hacker News."""
    jobs = []
    kw_lower = [k.lower() for k in keywords]
    try:
        # Get latest "Who is hiring" post
        r = httpx.get("https://hacker-news.firebaseio.com/v0/user/whoishiring.json", timeout=10)
        # Search for latest hiring thread via Algolia HN search
        search_r = httpx.get(
            "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=story,author_whoishiring&hitsPerPage=1",
            timeout=10
        )
        hits = search_r.json().get("hits", [])
        if not hits: return jobs
        story_id = hits[0]["objectID"]

        # Get comments
        story_r = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10)
        story = story_r.json()
        kids = story.get("kids", [])[:80]

        for kid_id in kids[:40]:
            try:
                c = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json", timeout=6).json()
                text = BeautifulSoup(c.get("text",""),"html.parser").get_text()[:1500]
                if any(k in text.lower() for k in kw_lower):
                    # Extract company name from first line
                    first_line = text.split("\n")[0][:80]
                    jobs.append({
                        "title": "See description", "company": first_line,
                        "url": f"https://news.ycombinator.com/item?id={kid_id}",
                        "description": text, "source": "YCombinator", "date": ""
                    })
            except: continue
    except Exception as e:
        st.warning(f"YC: {e}")
    return jobs[:10]

def scrape_greenhouse_lever(keywords):
    """Search Greenhouse and Lever job boards via their public APIs."""
    jobs = []
    kw_lower = [k.lower() for k in keywords]

    # Top AI/tech companies on Greenhouse
    greenhouse_companies = [
        "anthropic","openai","scale-ai","huggingface","cohere","mistral",
        "replicate","together","anyscale","modal","runway","perplexity"
    ]
    for company in greenhouse_companies:
        try:
            r = httpx.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true", timeout=8)
            if r.status_code != 200: continue
            data = r.json()
            for job in data.get("jobs", []):
                title = job.get("title","")
                content = BeautifulSoup(job.get("content",""),"html.parser").get_text()[:1500]
                if any(k in f"{title} {content}".lower() for k in kw_lower):
                    jobs.append({
                        "title": title, "company": company.title(),
                        "url": job.get("absolute_url",""),
                        "description": f"{title}\n\n{content}",
                        "source": "Greenhouse", "date": ""
                    })
        except: continue

    # Top companies on Lever
    lever_companies = ["openai","scale","cohere","weights-biases","together-ai"]
    for company in lever_companies:
        try:
            r = httpx.get(f"https://api.lever.co/v0/postings/{company}?mode=json", timeout=8)
            if r.status_code != 200: continue
            for job in r.json():
                title = job.get("text","")
                desc = BeautifulSoup(job.get("descriptionPlain",""),"html.parser").get_text()[:1500]
                if any(k in f"{title} {desc}".lower() for k in kw_lower):
                    jobs.append({
                        "title": title, "company": company.title(),
                        "url": job.get("hostedUrl",""),
                        "description": f"{title}\n\n{desc}",
                        "source": "Lever", "date": ""
                    })
        except: continue

    return jobs[:15]

def fetch_full_job_text(url: str) -> str:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=12)
        soup = BeautifulSoup(r.text,"html.parser")
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]): tag.decompose()
        signals = ["job-description","jobDescription","description","job-details","responsibilities","qualifications","show-more-less-html"]
        block = None
        for s in signals:
            block = soup.find(id=re.compile(s,re.I)) or soup.find(class_=re.compile(s,re.I))
            if block: break
        text = block.get_text("\n",strip=True) if block else soup.get_text("\n",strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip() and len(l.strip())>2]
        return "\n".join(lines)[:3000]
    except: return ""

# ── AI Scorer ─────────────────────────────────────────────────────────────────
def run_agent(job_text: str) -> dict:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key: raise ValueError("GROQ_API_KEY not set")
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":f"Evaluate this job and produce the full JSON output:\n\n{job_text[:2500]}"}
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*","",raw)
    raw = re.sub(r"\s*```$","",raw)
    return json.loads(raw)

# ── Resume PDF Generator ──────────────────────────────────────────────────────
def generate_resume_pdf(tailored_bullets: list, job_title: str, company: str, matched_keywords: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Styles
    accent = colors.HexColor("#6c63ff")
    dark = colors.HexColor("#1a1a2e")

    name_style = ParagraphStyle("name", fontSize=22, fontName="Helvetica-Bold",
        textColor=dark, spaceAfter=2, alignment=TA_CENTER)
    title_style = ParagraphStyle("title", fontSize=10, fontName="Helvetica",
        textColor=accent, spaceAfter=4, alignment=TA_CENTER)
    contact_style = ParagraphStyle("contact", fontSize=8, fontName="Helvetica",
        textColor=colors.HexColor("#555555"), spaceAfter=2, alignment=TA_CENTER)
    section_style = ParagraphStyle("section", fontSize=11, fontName="Helvetica-Bold",
        textColor=accent, spaceBefore=10, spaceAfter=3)
    body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica",
        textColor=dark, spaceAfter=3, leading=13)
    bullet_style = ParagraphStyle("bullet", fontSize=9, fontName="Helvetica",
        textColor=dark, spaceAfter=3, leading=13, leftIndent=12, bulletIndent=0)
    company_style = ParagraphStyle("company", fontSize=10, fontName="Helvetica-Bold",
        textColor=dark, spaceAfter=1)
    small_style = ParagraphStyle("small", fontSize=8, fontName="Helvetica",
        textColor=colors.HexColor("#888888"), spaceAfter=4)

    story = []
    p = VAULT["personal"]

    # Header
    story.append(Paragraph(p["name"], name_style))
    story.append(Paragraph(p["title"], title_style))
    story.append(Paragraph(
        f"{p['email']}  ·  {p['phone']}  ·  {p['location']}  ·  {p['linkedin']}  ·  {p['github']}",
        contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=6))

    # Tailored for note
    story.append(Paragraph(f"Tailored for: {job_title} at {company}", small_style))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    story.append(Paragraph(VAULT["summary"], body_style))

    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    skills = VAULT["skills"]
    skill_lines = [
        f"<b>Languages:</b> {', '.join(skills['languages'])}",
        f"<b>LLM & AI:</b> {', '.join(skills['llm_ai'])}",
        f"<b>Frameworks:</b> {', '.join(skills['frameworks'])}",
        f"<b>Vector/Retrieval:</b> {', '.join(skills['vector_retrieval'])}",
        f"<b>Infrastructure:</b> {', '.join(skills['infrastructure'])}",
        f"<b>Libraries:</b> {', '.join(skills['libraries'])}",
    ]
    for line in skill_lines:
        story.append(Paragraph(line, body_style))

    # Experience — use tailored bullets
    story.append(Paragraph("EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    exp = VAULT["experience"][0]
    story.append(Paragraph(f"{exp['title']} | {exp['company']}", company_style))
    story.append(Paragraph(f"{exp['dates']} · {exp['location']}", small_style))

    bullets_to_use = tailored_bullets if tailored_bullets else exp["bullets"]
    for b in bullets_to_use[:5]:
        story.append(Paragraph(f"• {b}", bullet_style))

    # Projects
    story.append(Paragraph("PROJECTS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    for proj in VAULT["projects"]:
        story.append(Paragraph(f"{proj['name']}  |  {proj['url']}", company_style))
        story.append(Paragraph(f"Stack: {', '.join(proj['stack'])}", small_style))
        for b in proj["bullets"]:
            story.append(Paragraph(f"• {b}", bullet_style))
        story.append(Spacer(1, 4))

    # Education
    story.append(Paragraph("EDUCATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    edu = VAULT["education"][0]
    story.append(Paragraph(f"{edu['degree']} · {edu['school']} · {edu['dates']}", body_style))

    # Certifications
    story.append(Paragraph("CERTIFICATIONS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceAfter=4))
    for cert in VAULT["certifications"]:
        story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()

# ── Email Digest ──────────────────────────────────────────────────────────────
def send_email_digest(tracker, smtp_user, smtp_pass, to_email):
    today = date.today().isoformat()
    today_jobs = [j for j in tracker if j.get("date")==today]
    applies = [j for j in today_jobs if j.get("decision")=="APPLY"]
    skips   = [j for j in today_jobs if j.get("decision")=="SKIP"]
    html = f"""<html><body style="font-family:Arial,sans-serif;background:#0a0a0f;color:#e8e8f0;padding:2rem;">
    <h2 style="color:#6c63ff;">🎯 Full Auto Job Agent — Daily Digest</h2>
    <p style="color:#aaa;">{today} · {len(today_jobs)} jobs evaluated · {len(applies)} matches</p>
    <hr style="border-color:#2a2a3f;">
    <h3 style="color:#00e676;">✅ APPLY ({len(applies)} matches)</h3>
    {''.join(f"""<div style="background:#12121a;border-left:3px solid #00e676;border-radius:8px;padding:1rem;margin-bottom:1rem;">
      <strong style="color:#fff;">{j['title']}</strong> @ {j['company']}<br>
      <span style="color:#6c63ff;font-weight:700;">{j['match_score']}% match</span>
      <span style="color:#aaa;font-size:0.85em;margin-left:1rem;">{j['source']}</span><br>
      <a href="{j['url']}" style="color:#6c63ff;">Open Application →</a><br>
      <em style="color:#888;font-size:0.85em;">{j.get('sheet_log','')}</em>
    </div>""" for j in applies) if applies else "<p style='color:#888;'>No matches today.</p>"}
    <h3 style="color:#ff5252;">❌ SKIPPED ({len(skips)})</h3>
    {''.join(f"<p style='color:#888;font-size:0.85em;'>• {j['title']} @ {j['company']} — {j.get('skip_reason','')[:80]}</p>" for j in skips[:5])}
    <hr style="border-color:#2a2a3f;">
    <p style="color:#555;font-size:0.75em;">Full Auto Job Agent v4 · {VAULT['personal']['name']}</p>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 Job Agent: {len(applies)} matches today ({today})"
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html,"html"))
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())

# ── Background Scheduler ──────────────────────────────────────────────────────
def run_auto_scan(keywords, sources, status_callback=None):
    """Run a full scan — called by scheduler or manual trigger."""
    all_jobs = []
    if "RemoteOK" in sources:
        j = scrape_remoteok(keywords); all_jobs.extend(j)
    if "WeWorkRemotely" in sources:
        j = scrape_weworkremotely(keywords); all_jobs.extend(j)
    if "LinkedIn" in sources:
        j = scrape_linkedin(keywords); all_jobs.extend(j)
    if "YCombinator" in sources:
        j = scrape_ycombinator(keywords); all_jobs.extend(j)
    if "Greenhouse/Lever" in sources:
        j = scrape_greenhouse_lever(keywords); all_jobs.extend(j)

    seen = set(); unique = []
    for j in all_jobs:
        key = j.get("url") or j.get("title","")
        if key and key not in seen:
            seen.add(key); unique.append(j)

    results = {"scanned":0,"applied":0,"skipped":0,"errors":0,"matches":[]}
    for job in unique:
        if already_tracked(job.get("url","")): continue
        job_text = job.get("description","")
        if job.get("url") and len(job_text)<300:
            full = fetch_full_job_text(job["url"])
            if full: job_text = full
        if not job_text.strip(): continue
        try:
            result = run_agent(job_text)
            log_application(job, result)
            results["scanned"] += 1
            if result.get("decision")=="APPLY":
                results["applied"] += 1
                results["matches"].append({"title":job["title"],"company":job["company"],
                    "url":job["url"],"score":result.get("match_score",0)})
            else:
                results["skipped"] += 1
            time.sleep(0.6)
        except Exception as e:
            results["errors"] += 1
    return results

def scheduler_loop(keywords, sources, interval_hours, stop_event):
    """Background thread that runs scans on a schedule."""
    while not stop_event.is_set():
        try:
            run_auto_scan(keywords, sources)
            # Log scan time
            if os.path.exists("scheduler_log.json"):
                with open("scheduler_log.json") as f: log = json.load(f)
            else: log = []
            log.insert(0, {"time": datetime.now().isoformat(), "status": "completed"})
            with open("scheduler_log.json","w") as f: json.dump(log[:20], f)
        except: pass
        stop_event.wait(timeout=interval_hours * 3600)

# ── Session State ─────────────────────────────────────────────────────────────
if "scan_log" not in st.session_state: st.session_state.scan_log = []
if "is_scanning" not in st.session_state: st.session_state.is_scanning = False
if "scheduler_running" not in st.session_state: st.session_state.scheduler_running = False
if "stop_event" not in st.session_state: st.session_state.stop_event = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:1.5rem 0 0.5rem;">
  <h1 style="font-family:'Syne',sans-serif;font-weight:800;font-size:2.2rem;margin:0;
             background:linear-gradient(90deg,#6c63ff,#ff6584);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    🎯 Full Auto Job Agent v4
  </h1>
  <p style="color:#666;font-family:'JetBrains Mono',monospace;font-size:0.8rem;margin:0.3rem 0 0;">
    {VAULT['personal']['name']} · {VAULT['personal']['location']} · 80% Gate · llama-3.3-70b · 5 Job Boards
  </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤖 Auto Hunt", "🔍 Single Job", "📊 Tracker", "⏰ Scheduler", "⚙️ Settings"])

# ════════════════════════════════════════════════════════════════════
# TAB 1: AUTO HUNT
# ════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Live Job Hunt")
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        keywords_input = st.text_input("Keywords (comma-separated)",
            value="AI Engineer, Prompt Engineer, LLM, RAG, Python")
    with col_cfg2:
        sources = st.multiselect("Job boards",
            ["RemoteOK","WeWorkRemotely","LinkedIn","YCombinator","Greenhouse/Lever"],
            default=["RemoteOK","WeWorkRemotely","LinkedIn","YCombinator"])

    tracker_data = load_tracker()
    applies_total = sum(1 for j in tracker_data if j.get("decision")=="APPLY")
    skips_total   = sum(1 for j in tracker_data if j.get("decision")=="SKIP")
    today_count   = sum(1 for j in tracker_data if j.get("date")==date.today().isoformat())

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-val">{len(tracker_data)}</div><div class="metric-label">Total Evaluated</div></div>',unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#00e676">{applies_total}</div><div class="metric-label">Matches</div></div>',unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#ff5252">{skips_total}</div><div class="metric-label">Skipped</div></div>',unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#ffd740">{today_count}</div><div class="metric-label">Today</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    if st.button("🚀 Start Auto Hunt", use_container_width=True, type="primary", disabled=st.session_state.is_scanning):
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        st.session_state.is_scanning = True
        st.session_state.scan_log = []

        log_box = st.empty()
        progress = st.progress(0)
        results_box = st.container()

        all_jobs = []
        log_box.markdown('<div class="status-bar">⚡ Scraping job boards...</div>',unsafe_allow_html=True)

        if "RemoteOK" in sources:
            j = scrape_remoteok(keywords); all_jobs.extend(j)
            st.session_state.scan_log.append(f"RemoteOK: {len(j)} jobs")
        if "WeWorkRemotely" in sources:
            j = scrape_weworkremotely(keywords); all_jobs.extend(j)
            st.session_state.scan_log.append(f"WeWorkRemotely: {len(j)} jobs")
        if "LinkedIn" in sources:
            j = scrape_linkedin(keywords); all_jobs.extend(j)
            st.session_state.scan_log.append(f"LinkedIn: {len(j)} jobs")
        if "YCombinator" in sources:
            j = scrape_ycombinator(keywords); all_jobs.extend(j)
            st.session_state.scan_log.append(f"YCombinator: {len(j)} jobs")
        if "Greenhouse/Lever" in sources:
            j = scrape_greenhouse_lever(keywords); all_jobs.extend(j)
            st.session_state.scan_log.append(f"Greenhouse/Lever: {len(j)} jobs")

        seen=set(); unique=[]
        for j in all_jobs:
            key=j.get("url") or j.get("title","")
            if key and key not in seen: seen.add(key); unique.append(j)

        new_jobs = [j for j in unique if not already_tracked(j.get("url",""))]
        st.session_state.scan_log.append(f"Unique new jobs: {len(new_jobs)} (skipping {len(unique)-len(new_jobs)} already seen)")

        if not new_jobs:
            st.info("No new jobs found. Try different keywords or check back later.")
            st.session_state.is_scanning = False
        else:
            apply_count = skip_count = 0
            for i, job in enumerate(new_jobs):
                pct = int((i/len(new_jobs))*100)
                progress.progress(pct)
                log_box.markdown(
                    f'<div class="status-bar">🔍 [{i+1}/{len(new_jobs)}] {job["title"][:50]} @ {job["company"][:25]}...</div>',
                    unsafe_allow_html=True)

                job_text = job.get("description","")
                if job.get("url") and len(job_text)<300:
                    full = fetch_full_job_text(job["url"])
                    if full: job_text = full
                if not job_text.strip(): continue

                try:
                    result = run_agent(job_text)
                    log_application(job, result)
                    if result.get("decision")=="APPLY":
                        apply_count+=1
                        score=result.get("match_score",0)
                        st.session_state.scan_log.append(f"✅ {score}% — {job['title']} @ {job['company']}")
                        with results_box:
                            st.success(f"✅ **{score}%** — {job['title']} at **{job['company']}** [{job['source']}]")
                            if job.get("url"):
                                st.markdown(f"[Open application →]({job['url']})")
                    else:
                        skip_count+=1
                        st.session_state.scan_log.append(f"❌ {result.get('match_score',0)}% — {job['title']}")
                    time.sleep(0.5)
                except json.JSONDecodeError:
                    st.session_state.scan_log.append(f"⚠ JSON error: {job['title']}")
                except Exception as e:
                    st.session_state.scan_log.append(f"⚠ Error: {str(e)[:60]}")

            progress.progress(100)
            log_box.markdown(
                f'<div class="status-bar">✅ Done — {apply_count} matches · {skip_count} skipped · {len(new_jobs)} total</div>',
                unsafe_allow_html=True)
            st.session_state.is_scanning = False
            if apply_count > 0: st.balloons()

    if st.session_state.scan_log:
        with st.expander("📋 Scan log"):
            for line in st.session_state.scan_log: st.text(line)

# ════════════════════════════════════════════════════════════════════
# TAB 2: SINGLE JOB + APPLY ASSISTANT + RESUME PDF
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Single Job Evaluator")
    col1, col2 = st.columns([2,1])

    with col1:
        method = st.radio("Input:", ["Paste URL","Paste description"], horizontal=True)
        job_text_m = None; job_url_m = ""
        if method=="Paste URL":
            job_url_m = st.text_input("Job URL", placeholder="https://boards.greenhouse.io/...")
            if job_url_m:
                with st.spinner("Reading..."):
                    try:
                        job_text_m = fetch_full_job_text(job_url_m)
                        st.success(f"✓ {len(job_text_m):,} chars")
                        with st.expander("Preview"): st.text(job_text_m[:400]+"...")
                    except Exception as e: st.error(str(e))
        else:
            job_text_m = st.text_area("Paste job description", height=220)

    with col2:
        st.subheader("Career Vault")
        st.success(f"✓ {VAULT['personal']['name']}")
        st.caption(f"📍 {VAULT['personal']['location']}")
        st.caption(f"🔧 {len(VAULT['skills']['llm_ai'])} LLM skills")
        st.caption(f"🚀 {len(VAULT['projects'])} live projects")
        st.info("80% gate active")

    if st.button("🎯 Evaluate + Prepare Full Package", use_container_width=True, type="primary"):
        if not job_text_m:
            st.error("Provide a URL or description.")
        else:
            with st.spinner("Scoring and preparing package..."):
                try:
                    result = run_agent(job_text_m)
                    score = result.get("match_score",0)
                    decision = result.get("decision","SKIP")
                    breakdown = result.get("score_breakdown",{})
                    job_meta = {"title":"Manual Entry","company":"Unknown","url":job_url_m,"source":"Manual"}
                    log_application(job_meta, result)

                    ca,cb,cc,cd = st.columns(4)
                    ca.metric("Match Score", f"{score}%")
                    cb.metric("Decision", decision)
                    cc.metric("Technical", f"{breakdown.get('technical_skills',0)}/40")
                    cd.metric("Seniority", f"{breakdown.get('seniority_experience',0)}/30")

                    if decision=="SKIP":
                        st.error("❌ SKIPPED — Below 80% gate")
                        st.warning(result.get("skip_reason","Score too low"))
                        st.info("Missing: " + ", ".join(result.get("missing_keywords",[])))
                    else:
                        st.success(f"✅ APPLYING — {score}% match!")

                        with st.expander("📝 Tailored resume bullets", expanded=True):
                            for b in result.get("tailored_bullets",[]): st.markdown(f"• {b}")

                        with st.expander("✉️ Cover letter", expanded=True):
                            st.text_area("", result.get("cover_letter",""), height=160, label_visibility="collapsed")

                        with st.expander("💬 Screening answers", expanded=True):
                            for q,a in result.get("screening_answers",{}).items():
                                st.markdown(f"**{q}**"); st.code(a, language=None)

                        with st.expander("🖊️ One-Click Apply Assistant", expanded=True):
                            st.markdown("**Pre-filled application form answers — copy and paste:**")
                            p = VAULT["personal"]
                            st.markdown(f"""
| Field | Your Answer |
|-------|-------------|
| Full Name | {p['name']} |
| Email | {p['email']} |
| Phone | {p['phone']} |
| Location | {p['location']} |
| LinkedIn URL | https://{p['linkedin']} |
| GitHub URL | https://{p['github']} |
| Work Authorization | {VAULT['preferences']['work_auth']} |
| Available Start Date | {VAULT['preferences']['available']} |
| Salary Expectation | {VAULT['preferences']['salary']} |
| Remote Work | Yes |
""")
                            st.markdown("**Cover letter (ready to paste):**")
                            st.code(result.get("cover_letter",""), language=None)
                            if job_url_m:
                                st.link_button("🔗 Open Application Form →", job_url_m, use_container_width=True, type="primary")

                        # Resume PDF
                        with st.expander("📄 Tailored Resume PDF", expanded=True):
                            st.caption("Generates a resume with your tailored bullets for this specific job")
                            if st.button("Generate Tailored Resume PDF", type="secondary"):
                                with st.spinner("Building PDF..."):
                                    pdf_bytes = generate_resume_pdf(
                                        tailored_bullets=result.get("tailored_bullets",[]),
                                        job_title="Target Role",
                                        company="Target Company",
                                        matched_keywords=result.get("matched_keywords",[])
                                    )
                                    st.download_button(
                                        "⬇ Download Resume PDF",
                                        data=pdf_bytes,
                                        file_name=f"Tirumalarao_Kilari_Resume_{score}pct.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )

                except json.JSONDecodeError:
                    st.error("Agent returned invalid JSON. Try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ════════════════════════════════════════════════════════════════════
# TAB 3: TRACKER
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Application Tracker")
    tracker_data = load_tracker()

    if not tracker_data:
        st.info("No applications tracked yet. Run Auto Hunt to start.")
    else:
        applies = [j for j in tracker_data if j.get("decision")=="APPLY"]
        skips   = [j for j in tracker_data if j.get("decision")=="SKIP"]
        avg_score = sum(j.get("match_score",0) for j in tracker_data) // max(len(tracker_data),1)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", len(tracker_data))
        c2.metric("Matches", len(applies))
        c3.metric("Skipped", len(skips))
        c4.metric("Avg Score", f"{avg_score}%")

        st.markdown("---")
        f1,f2 = st.columns(2)
        with f1: fd = st.selectbox("Decision", ["All","APPLY","SKIP"])
        with f2: fs = st.selectbox("Source", ["All"]+list(set(j.get("source","") for j in tracker_data)))

        filtered = tracker_data
        if fd!="All": filtered=[j for j in filtered if j.get("decision")==fd]
        if fs!="All": filtered=[j for j in filtered if j.get("source")==fs]

        st.caption(f"Showing {len(filtered)} entries")

        for job in filtered[:50]:
            decision=job.get("decision","SKIP"); score=job.get("match_score",0)
            icon = "✅" if decision=="APPLY" else "❌"
            with st.expander(f"{icon} {score}% — {job['title']} @ {job['company']} [{job.get('source','')}]"):
                c_a,c_b = st.columns([3,1])
                with c_a:
                    st.caption(f"📅 {job.get('timestamp','')[:19]} · {job.get('source','')} · {job.get('url','')[:55]}")
                    if decision=="APPLY":
                        st.markdown("**Keywords:** " + " ".join([f"`{k}`" for k in job.get("matched_keywords",[])[:8]]))
                        if job.get("tailored_bullets"):
                            st.markdown(f"**Top bullet:** {job['tailored_bullets'][0]}")

                        # Generate PDF directly from tracker
                        if st.button(f"📄 Download Resume PDF", key=f"pdf_{job['id']}"):
                            pdf_bytes = generate_resume_pdf(
                                job.get("tailored_bullets",[]), job["title"], job["company"],
                                job.get("matched_keywords",[]))
                            st.download_button("⬇ Download", data=pdf_bytes,
                                file_name=f"Resume_{job['company']}_{score}pct.pdf",
                                mime="application/pdf", key=f"dl_{job['id']}")

                        if job.get("url"): st.link_button("Open Application →", job["url"])
                    else:
                        st.warning(f"Skip: {job.get('skip_reason','')}")
                with c_b:
                    bd=job.get("score_breakdown",{})
                    st.metric("Technical",f"{bd.get('technical_skills',0)}/40")
                    st.metric("Seniority",f"{bd.get('seniority_experience',0)}/30")
                    st.metric("Industry",f"{bd.get('industry_alignment',0)}/30")

        st.markdown("---")
        if st.button("⬇ Export JSON", use_container_width=True):
            st.download_button("Download", data=json.dumps(tracker_data,indent=2),
                file_name=f"applications_{date.today().isoformat()}.json", mime="application/json")

# ════════════════════════════════════════════════════════════════════
# TAB 4: SCHEDULER
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("⏰ Auto-Scheduler")
    st.caption("Runs a full scan automatically on a set interval — no button click needed")

    if st.session_state.scheduler_running:
        st.markdown('<div class="sched-active">🟢 Scheduler is ACTIVE — scanning automatically</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-bar">⭕ Scheduler is STOPPED</div>',unsafe_allow_html=True)

    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        sched_keywords = st.text_input("Scheduler keywords",
            value="AI Engineer, Prompt Engineer, LLM, RAG, Python", key="sched_kw")
        sched_interval = st.selectbox("Scan interval", [1,2,4,6,12,24],
            index=3, format_func=lambda x: f"Every {x} hour{'s' if x>1 else ''}")
    with col_sc2:
        sched_sources = st.multiselect("Boards to scan",
            ["RemoteOK","WeWorkRemotely","LinkedIn","YCombinator","Greenhouse/Lever"],
            default=["RemoteOK","WeWorkRemotely","YCombinator"], key="sched_src")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶ Start Scheduler", use_container_width=True, type="primary",
                     disabled=st.session_state.scheduler_running):
            kw = [k.strip() for k in sched_keywords.split(",") if k.strip()]
            stop_event = threading.Event()
            st.session_state.stop_event = stop_event
            t = threading.Thread(target=scheduler_loop,
                args=(kw, sched_sources, sched_interval, stop_event), daemon=True)
            t.start()
            st.session_state.scheduler_running = True
            st.success(f"✅ Scheduler started — scanning every {sched_interval}h")
            st.rerun()

    with col_btn2:
        if st.button("⏹ Stop Scheduler", use_container_width=True,
                     disabled=not st.session_state.scheduler_running):
            if st.session_state.stop_event:
                st.session_state.stop_event.set()
            st.session_state.scheduler_running = False
            st.info("Scheduler stopped.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔁 Manual Trigger")
    st.caption("Run one scan right now without the scheduler")
    if st.button("▶ Run One Scan Now", use_container_width=True):
        kw = [k.strip() for k in sched_keywords.split(",") if k.strip()]
        with st.spinner("Running scan..."):
            results = run_auto_scan(kw, sched_sources)
        st.success(f"Scan complete — {results['applied']} matches, {results['skipped']} skipped, {results['scanned']} evaluated")
        if results["matches"]:
            for m in results["matches"]:
                st.success(f"✅ {m['score']}% — {m['title']} @ {m['company']}")

    # Scheduler log
    if os.path.exists("scheduler_log.json"):
        with open("scheduler_log.json") as f:
            sched_log = json.load(f)
        if sched_log:
            st.markdown("#### 📋 Last scan times")
            for entry in sched_log[:5]:
                st.caption(f"🕐 {entry['time'][:19]} — {entry['status']}")

    st.markdown("---")
    st.info("""
**Important note about Render free tier:**
Render free instances spin down after 15 minutes of inactivity. The scheduler thread runs inside the Streamlit process — if the app spins down, the scheduler stops too.

**To keep it always-on:**
- Upgrade to Render Starter ($7/mo) — always-on instances
- Or use a free uptime pinger like UptimeRobot to ping your URL every 5 minutes
""")

# ════════════════════════════════════════════════════════════════════
# TAB 5: SETTINGS
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Settings & Email Digest")

    st.markdown("#### 📧 Email Digest")
    with st.form("email_form"):
        smtp_user = st.text_input("Your Gmail", placeholder="youremail@gmail.com")
        smtp_pass = st.text_input("Gmail App Password", type="password",
            help="myaccount.google.com/apppasswords — NOT your regular password")
        to_email  = st.text_input("Send to", value=VAULT["personal"]["email"])
        send_btn  = st.form_submit_button("📨 Send Today's Digest", use_container_width=True)

    if send_btn:
        if not smtp_user or not smtp_pass:
            st.error("Enter Gmail + App Password")
        else:
            with st.spinner("Sending..."):
                try:
                    send_email_digest(load_tracker(), smtp_user, smtp_pass, to_email)
                    st.success(f"✅ Sent to {to_email}")
                except Exception as e:
                    st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("#### ℹ️ Gmail App Password setup")
    st.markdown("""
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Create → name it "Job Agent"
3. Copy the 16-char password → paste above
""")

    st.markdown("---")
    st.markdown("#### 🗑️ Clear Tracker")
    if st.button("Clear all tracked applications", type="secondary"):
        save_tracker([])
        st.success("Cleared."); st.rerun()

    st.markdown("---")
    st.caption(f"Full Auto Job Agent v4 · {VAULT['personal']['name']} · llama-3.3-70b · 5 boards · Resume PDF · Scheduler")
