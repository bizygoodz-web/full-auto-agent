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

# Load career vault
with open("career_vault.json") as f:
    VAULT = json.load(f)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

SYSTEM_PROMPT = f"""You are the Lead Systems Architect and Career Strategist for a Full Auto Premium Job Agent.

CAREER VAULT (USE ONLY THESE FACTS — ZERO HALLUCINATION):
{json.dumps(VAULT, indent=2)}

RULES:
1. NEVER invent skills, experience, or facts not in the Career Vault
2. If match score < 80, output ONLY decision SKIP with detailed skip_reason
3. Map Vault language to JD language (e.g. if JD says "Orchestrated" and Vault says "Managed", use "Orchestrated")
4. Respond ONLY with valid JSON — no markdown fences, no extra text

SCORING WEIGHTS:
- 40% Technical/Hard Skills match
- 30% Role Seniority/Experience match  
- 30% Industry Alignment

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
    "Tell me about yourself": "2-3 sentence answer using vault data",
    "Why do you want this role": "2-3 sentence answer",
    "What is your greatest strength": "2-3 sentence answer relevant to JD"
  }},
  "sheet_log": "One sentence daily log summary e.g. Applied: 88% Match - Strong alignment with X requirements"
}}"""

def scrape_job(url: str) -> str:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
            tag.decompose()
        signals = ["job-description","jobDescription","description","job-details","responsibilities","qualifications","about-the-role"]
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
            {"role": "user", "content": f"Evaluate this job and produce the full JSON output:\n\n{job_text}"}
        ],
        max_tokens=2500
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

# ── UI ──────────────────────────────────────────────────────────────────────

st.title("🎯 Full Auto Premium Job Agent")
st.caption(f"Candidate: {VAULT['personal']['name']} · {VAULT['personal']['location']} · 80% Match Gate Active")
st.markdown("---")

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Job Input")
    input_method = st.radio("How do you want to input the job?", ["Paste URL", "Paste job description text"], horizontal=True)

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
        job_text = st.text_area("Paste full job description", height=250, placeholder="Paste the complete job description here...")

with col2:
    st.subheader("Career Vault")
    st.success(f"✓ {VAULT['personal']['name']}")
    st.caption(f"📍 {VAULT['personal']['location']}")
    st.caption(f"🔧 {len(VAULT['skills']['llm_ai'])} LLM skills")
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

                # Score display
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Match Score", f"{score}%")
                col_b.metric("Decision", decision)
                breakdown = result.get("score_breakdown", {})
                col_c.metric("Technical", f"{breakdown.get('technical_skills', 0)}/40")
                col_d.metric("Seniority", f"{breakdown.get('seniority_experience', 0)}/30")

                if decision == "SKIP":
                    st.error("❌ SKIPPED — Score below 80% gate")
                    st.warning(f"**Skip reason:** {result.get('skip_reason', 'Score too low')}")
                    st.info("**Missing keywords:** " + ", ".join(result.get("missing_keywords", [])))

                else:
                    st.success(f"✅ APPLYING — {score}% match clears the 80% gate!")

                    # Matched keywords
                    st.markdown("**Matched keywords:**")
                    st.markdown(" ".join([f"`{k}`" for k in result.get("matched_keywords", [])]))

                    # Tailored bullets
                    with st.expander("📝 Tailored resume bullets", expanded=True):
                        for b in result.get("tailored_bullets", []):
                            st.markdown(f"• {b}")

                    # Cover letter
                    with st.expander("✉️ Cover letter (150 words)", expanded=True):
                        st.text_area("", result.get("cover_letter", ""), height=180, label_visibility="collapsed")

                    # Screening answers
                    with st.expander("💬 Screening answers", expanded=True):
                        for q, a in result.get("screening_answers", {}).items():
                            st.markdown(f"**{q}**")
                            st.code(a, language=None)

                    # Daily log
                    st.markdown("---")
                    st.markdown("**📊 Daily sheet log:**")
                    st.info(result.get("sheet_log", ""))

                    # Open job
                    if job_url:
                        st.link_button("🔗 Open job application →", job_url, use_container_width=True, type="primary")

                    # Download full package
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
{result.get('cover_letter', '')}

SCREENING ANSWERS:
{chr(10).join(f"Q: {q}{chr(10)}A: {a}{chr(10)}" for q,a in result.get('screening_answers', {}).items())}

DAILY LOG:
{result.get('sheet_log', '')}

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

                    st.download_button(
                        "⬇ Download full application package",
                        package,
                        file_name=f"application_{score}pct.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

            except json.JSONDecodeError as e:
                st.error(f"Agent returned invalid JSON. Try again — {e}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("---")
st.caption(f"Built by {VAULT['personal']['name']} · AI Engineer · Full Auto Job Agent v1.0")
