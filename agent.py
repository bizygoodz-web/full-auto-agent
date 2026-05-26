import streamlit as st
from groq import Groq
import httpx
from bs4 import BeautifulSoup
import json
import re
import os

st.set_page_config(
    page_title="Full Auto Job Agent",
    page_icon="🎯",
    layout="wide"
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
      "name": "ResumeAI",
      "url": "resumeai-v2.onrender.com",
      "stack": ["Python", "Streamlit", "Groq", "BeautifulSoup", "Render"],
      "bullets": [
        "Built and deployed full-stack AI web application that reads job posting URLs automatically and tailors resumes",
        "Multi-stage pipeline: URL scraping → skill gap analysis → resume rewriting → cover letter generation",
        "Live deployed on Render with PDF/DOCX parsing and real-time Groq LLaMA API calls"
      ]
    },
    {
      "name": "AI Agent with Web Search",
      "url": "my-ai-agent-app.onrender.com",
      "stack": ["Python", "Streamlit", "Groq", "DuckDuckGo"],
      "bullets": [
        "Conversational AI agent with real-time web search using tool-use loop",
        "LLM decides whether to search, executes search, feeds results back, generates grounded answer",
        "Full multi-turn conversation memory with live search status indicators"
      ]
    },
    {
      "name": "RAG PDF Chat Agent",
      "url": "github.com/bizygoodz-web/rag-pdf-chat",
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

def scrape_job(url: str) -> str:
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

def run_agent(job_text: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Evaluate this job and produce the full JSON output:\n\n{job_text[:2000]}"}
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

# UI
st.title("🎯 Full Auto Premium Job Agent")
st.caption(f"Candidate: {VAULT['personal']['name']} · {VAULT['personal']['location']} · 80% Match Gate Active")
st.markdown("---")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Job Input")
    input_method = st.radio("Input method:", ["Paste URL", "Paste job description text"], horizontal=True)
    job_text = None
    job_url = ""

    if input_method == "Paste URL":
        job_url = st.text_input("Job posting URL", placeholder="https://boards.greenhouse.io/company/jobs/12345")
        if job_url:
            with st.spinner("Reading job page..."):
                try:
                    job_text = scrape_job(job_url)
                    st.success(f"✓ Job read — {len(job_text):,} chars")
                    with st.expander("Preview"):
                        st.text(job_text[:400] + "...")
                except Exception as e:
                    st.error(str(e))
    else:
        job_text = st.text_area("Paste full job description", height=250,
            placeholder="Paste the complete job description here...")

with col2:
    st.subheader("Career Vault")
    st.success(f"✓ {VAULT['personal']['name']}")
    st.caption(f"📍 {VAULT['personal']['location']}")
    st.caption(f"🔧 {len(VAULT['skills']['llm_ai'])} LLM skills loaded")
    st.caption(f"🚀 {len(VAULT['projects'])} live projects")
    st.caption(f"📋 {len(VAULT['experience'])} positions")
    st.info("80% gate active — low matches auto-skipped")

st.markdown("---")

if st.button("🚀 Evaluate & Prepare Application", use_container_width=True, type="primary"):
    if not job_text:
        st.error("Please provide a job URL or paste a job description.")
    else:
        with st.spinner("Agent evaluating match score and preparing full application package..."):
            try:
                result = run_agent(job_text)
                score = result.get("match_score", 0)
                decision = result.get("decision", "SKIP")
                breakdown = result.get("score_breakdown", {})

                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Match Score", f"{score}%")
                col_b.metric("Decision", decision)
                col_c.metric("Technical", f"{breakdown.get('technical_skills',0)}/40")
                col_d.metric("Seniority", f"{breakdown.get('seniority_experience',0)}/30")

                if decision == "SKIP":
                    st.error("❌ SKIPPED — Score below 80% gate")
                    st.warning(f"**Skip reason:** {result.get('skip_reason','Score too low')}")
                    st.info("**Missing:** " + ", ".join(result.get("missing_keywords", [])))
                else:
                    st.success(f"✅ APPLYING — {score}% match clears the 80% gate!")
                    st.markdown("**Matched:** " + " ".join([f"`{k}`" for k in result.get("matched_keywords", [])]))

                    with st.expander("📝 Tailored resume bullets", expanded=True):
                        for b in result.get("tailored_bullets", []):
                            st.markdown(f"• {b}")

                    with st.expander("✉️ Cover letter", expanded=True):
                        st.text_area("", result.get("cover_letter",""), height=180, label_visibility="collapsed")

                    with st.expander("💬 Screening answers", expanded=True):
                        for q, a in result.get("screening_answers", {}).items():
                            st.markdown(f"**{q}**")
                            st.code(a, language=None)

                    st.markdown("**📊 Daily log:** " + result.get("sheet_log",""))

                    if job_url:
                        st.link_button("🔗 Open job application →", job_url, use_container_width=True, type="primary")

                    package = f"""FULL AUTO JOB AGENT — APPLICATION PACKAGE
{'='*50}
CANDIDATE: {VAULT['personal']['name']}
JOB URL: {job_url or 'Manual input'}
MATCH SCORE: {score}%
DECISION: {decision}

SCORE BREAKDOWN:
Technical Skills: {breakdown.get('technical_skills',0)}/40
Seniority/Experience: {breakdown.get('seniority_experience',0)}/30
Industry Alignment: {breakdown.get('industry_alignment',0)}/30

MATCHED KEYWORDS:
{', '.join(result.get('matched_keywords', []))}

TAILORED BULLETS:
{chr(10).join('• ' + b for b in result.get('tailored_bullets', []))}

COVER LETTER:
{result.get('cover_letter','')}

SCREENING ANSWERS:
{chr(10).join(f"Q: {q}{chr(10)}A: {a}{chr(10)}" for q,a in result.get('screening_answers',{}).items())}

DAILY LOG: {result.get('sheet_log','')}

YOUR INFO:
Name: {VAULT['personal']['name']}
Email: {VAULT['personal']['email']}
Phone: {VAULT['personal']['phone']}
Location: {VAULT['personal']['location']}
LinkedIn: {VAULT['personal']['linkedin']}
GitHub: {VAULT['personal']['github']}
Available: {VAULT['preferences']['available']}
Work Auth: {VAULT['preferences']['work_auth']}
Salary: {VAULT['preferences']['salary']}"""

                    st.download_button("⬇ Download full application package", package,
                        file_name=f"application_{score}pct.txt", mime="text/plain", use_container_width=True)

            except json.JSONDecodeError:
                st.error("Agent returned invalid JSON. Please try again.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("---")
st.caption(f"Built by {VAULT['personal']['name']} · Full Auto Job Agent v2.0")
