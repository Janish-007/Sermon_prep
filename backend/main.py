import os
import uuid
import re
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time
from dotenv import load_dotenv

# Import logger utilities
from app_logger import get_logger, set_request_id

# Load environment variables
load_dotenv()

GLOO_CLIENT_ID = os.getenv("GLOO_CLIENT_ID")
GLOO_CLIENT_SECRET = os.getenv("GLOO_CLIENT_SECRET")
GLOO_BASE_URL = os.getenv("GLOO_BASE_URL", "https://platform.ai.gloo.com").rstrip('/')
GLOO_TOKEN_URL = os.getenv("GLOO_TOKEN_URL", f"{GLOO_BASE_URL}/oauth2/token")
GLOO_PUBLISHER_ID = os.getenv("GLOO_PUBLISHER_ID")
GLOO_TENANT_NAME = os.getenv("GLOO_TENANT_NAME", "JustoInternal")
GLOO_COLLECTION = os.getenv("GLOO_COLLECTION", "GlooProd")
GLOO_SEARCH_URL = os.getenv("GLOO_SEARCH_URL", f"{GLOO_BASE_URL}/ai/data/v1/search")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

# Initialize logger
logger = get_logger()

# Token Caching
_gloo_token = None
_gloo_token_expiry = 0

def get_gloo_token() -> str:
    global _gloo_token, _gloo_token_expiry
    if _gloo_token and time.time() < _gloo_token_expiry:
        return _gloo_token
        
    if not GLOO_CLIENT_ID or not GLOO_CLIENT_SECRET:
        raise ValueError("GLOO_CLIENT_ID and GLOO_CLIENT_SECRET must be set.")
        
    logger.info("Fetching new Gloo OAuth token...")
    payload = {
        "grant_type": "client_credentials",
        "client_id": GLOO_CLIENT_ID,
        "client_secret": GLOO_CLIENT_SECRET
    }
    
    try:
        response = requests.post(GLOO_TOKEN_URL, data=payload)
        response.raise_for_status()
        data = response.json()
        _gloo_token = data.get("access_token")
        # Subtract 60 seconds as a buffer
        expires_in = data.get("expires_in", 3600)
        _gloo_token_expiry = time.time() + expires_in - 60 
        return _gloo_token
    except Exception as e:
        logger.error(f"Failed to fetch Gloo token: {e}")
        raise

# FastAPI app
app = FastAPI(
    title="Prayer and Promise API",
    description="Helps the user write their own prayer and provides comforting Bible promises using Gloo Native RAG.",
    version="1.0.0"
)

class QueryInput(BaseModel):
    query: str
    lang: Optional[str] = "en"

class SermonInput(BaseModel):
    topic: str
    scripture: Optional[str] = None
    style: Optional[str] = "Pastoral"
    duration: Optional[str] = "30 mins"
    audience: Optional[str] = "General Congregation"
    lang: Optional[str] = "en"

LANGUAGE_MAP = {
    "en": "English",
    "ta": "Tamil",
    "tamil": "Tamil",
    "english": "English"
}

# Parse promises utility
def parse_promises(promise_text):
    # Support standard quotes, smart quotes, and markdown formatting (like **"..."**)
    blocks = re.findall(r'[*_]*["“”](.+?)["“”][*_]*\s*\n+\s*([^\n]+)', promise_text.strip())
    promises = []
    for verse_text, reference in blocks[:10]:
        verse_text = re.sub(r'^Promise\s*\d+:?\s*', '', verse_text.strip(), flags=re.IGNORECASE)
        promises.append({
            "verse": f"\"{verse_text.strip()}\"",
            "reference": reference.strip()
        })
    return promises

# Relevance check removed to avoid 404 errors and simplify logic

# RAG Search Helpers
def search_gloo(query: str, limit: int = 10, certainty: float = 0.5) -> list[dict]:
    """Vector-search the Gloo knowledge base and return raw result items."""
    payload = {
        "query":      query,
        "collection": GLOO_COLLECTION,
        "tenant":     GLOO_TENANT_NAME,
        "certainty":  certainty,
        "limit":      limit,
    }
    headers = {
        "Authorization": f"Bearer {get_gloo_token()}",
        "Content-Type":  "application/json",
    }
    logger.info(f"Searching Gloo knowledge base for query: {query}")
    resp = requests.post(GLOO_SEARCH_URL, headers=headers, json=payload, timeout=15)
    if resp.status_code != 200:
        logger.error(f"Search error {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=502, detail=f"Gloo search error: {resp.text}")
    return resp.json().get("data", [])

def extract_snippets(results: list[dict], min_len: int = 50) -> list[str]:
    """Extract snippet texts from search results."""
    snippets = []
    for r in results:
        snippet = r.get("properties", {}).get("snippet", "").strip()
        if len(snippet) >= min_len:
            snippets.append(snippet)
    return snippets

# Combined logic using Gloo Two-Step RAG
def generate_prayer_and_promises(query: str, lang: str) -> dict:
    full_lang = LANGUAGE_MAP.get(lang.lower(), "English")
    url = f"{GLOO_BASE_URL}/ai/v2/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_gloo_token()}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Retrieve context
    try:
        results = search_gloo(query, limit=10, certainty=0.5)
        snippets = extract_snippets(results)
    except Exception as e:
        logger.warning(f"Gloo search failed, proceeding without context: {e}")
        snippets = []
    
    if not snippets:
        logger.info("No relevant snippets found in Gloo database.")
        context_text = "No direct context found."
    else:
        context_text = "\n\n".join(f"- {text}" for text in snippets)
    
    # Step 2: Build prompt
    system_message = (
        f"You are a compassionate Christian assistant. "
        f"The user has shared a situation or feeling. You need to do two things:\n\n"
        f"1. Help the user write a short, heartfelt prayer in their own words, based on what they shared. "
        f"The prayer should be from the perspective of the user speaking to God. Keep it under 2000 characters.\n\n"
        f"2. Provide ten comforting Bible promises relevant to their situation. "
        f"Base these promises primarily on the following context from the Bible if applicable:\n\n"
        f"Context:\n{context_text}\n\n"
        f"Format each promise exactly like this:\n"
        f"\"Blessed are those who mourn, for they will be comforted.\"\nMatthew 5:4\n\n"
        f"Always use the exact English word 'PROMISES' to separate the prayer and the Bible verses.\n"
        f"Respond entirely in {full_lang}."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_message},
            {
                "role": "user", 
                "content": f"The user has submitted the following safe prayer request/feeling:\n\n\"{query}\"\n\nPlease respond entirely in {full_lang}."
            }
        ],
        "temperature": 0.7,
        "auto_routing": True
    }
    
    logger.info("Calling standard Gloo chat completion with retrieved context")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        logger.error(f"Gloo API Error: {response.status_code} - {response.text}")
        response.raise_for_status()
        
    answer_text = response.json()["choices"][0]["message"]["content"].strip()
    
    logger.info(f"Raw Gloo Response:\n{answer_text}")
    
    # Extract PROMISES section
    parts = re.split(r'PROMISES', answer_text, flags=re.IGNORECASE, maxsplit=1)
    prayer = parts[0].strip()
    promises_raw = parts[1].strip() if len(parts) > 1 else answer_text
 
    return {
        "prayer": prayer[:2000],
        "promise": parse_promises(promises_raw)
    }

def get_prayer_and_promises(query: str, lang: str) -> dict:
    logger.info(f"Processing prayer & promises")
    return generate_prayer_and_promises(query, lang)

# --- SERMON PREPARATION ASSISTANT INTEGRATION ---

def parse_sermon_markdown(text: str) -> dict:
    """Parses Gloo AI custom sermon pack markdown output into structured dictionary."""
    result = {
        "title": "Custom Generated Sermon",
        "main_scripture": "Scripture Reference",
        "memory_verse": "Not Specified",
        "theme": "A customized sermon prep pack built specifically for your ministry needs.",
        "outline": "",
        "scriptures": [],
        "illustrations": [],
        "discussion_questions": [],
        "teaching_notes": ""
    }
    
    # Read headers
    title_match = re.search(r"^# TITLE:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    if title_match:
        result["title"] = title_match.group(1).strip()
        
    scripture_match = re.search(r"^# MAIN SCRIPTURE:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    if scripture_match:
        result["main_scripture"] = scripture_match.group(1).strip()
        
    mv_match = re.search(r"^# MEMORY VERSE:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    if mv_match:
        result["memory_verse"] = mv_match.group(1).strip()
        
    theme_match = re.search(r"^# CORE THEME:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    if theme_match:
        result["theme"] = theme_match.group(1).strip()
        
    # Split by sections
    sections = re.split(r"^## SECTION:\s*", text, flags=re.MULTILINE | re.IGNORECASE)
    
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
            
        lines = sec.split("\n")
        header = lines[0].strip().upper()
        content = "\n".join(lines[1:]).strip()
        
        if "OUTLINE" in header:
            result["outline"] = content
        elif "SCRIPTURES" in header:
            result["scriptures_raw"] = content
            items = re.split(r"^###\s*", content, flags=re.MULTILINE)
            for item in items:
                item = item.strip()
                if not item:
                    continue
                lines_item = item.split("\n")
                ref_line = lines_item[0].strip()
                text_line = "\n".join(lines_item[1:]).strip()
                
                # Extract role if present
                role = "Cross Reference"
                role_match = re.search(r"\(([^)]+)\)", ref_line)
                if role_match:
                    role = role_match.group(1)
                    ref_line = re.sub(r"\([^)]+\)", "", ref_line).strip()
                    
                result["scriptures"].append({
                    "ref": ref_line, 
                    "text": text_line, 
                    "role": role
                })
        elif "ILLUSTRATIONS" in header:
            result["illustrations_raw"] = content
            items = re.split(r"^###\s*", content, flags=re.MULTILINE)
            for item in items:
                item = item.strip()
                if not item:
                    continue
                lines_item = item.split("\n")
                title_line = lines_item[0].strip()
                body_item = "\n".join(lines_item[1:]).strip()
                
                badge = "Sermon Illustration"
                badge_match = re.search(r"\(([^)]+)\)", title_line)
                if badge_match:
                    badge = badge_match.group(1)
                    title_line = re.sub(r"\([^)]+\)", "", title_line).strip()
                
                story = ""
                app = ""
                
                story_match = re.search(r"\*Story\*:\s*(.*?)(?=\*Application\*|$)", body_item, re.DOTALL | re.IGNORECASE)
                app_match = re.search(r"\*Application\*:\s*(.*)$", body_item, re.DOTALL | re.IGNORECASE)
                
                if story_match:
                    story = story_match.group(1).strip()
                else:
                    story = body_item
                    
                if app_match:
                    app = app_match.group(1).strip()
                
                result["illustrations"].append({
                    "title": title_line,
                    "badge": badge,
                    "story": story,
                    "application": app
                })
        elif "DISCUSSION" in header:
            result["questions_raw"] = content
            q_lines = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)
            for ql in q_lines:
                ql = ql.strip()
                if ql:
                    result["discussion_questions"].append(ql)
        elif "TEACHING" in header:
            result["teaching_notes"] = content
            
    return result

def generate_sermon_pack(payload: SermonInput) -> dict:
    """Uses Gloo Ingestion RAG and completions to draft a full sermon preparation package."""
    full_lang = LANGUAGE_MAP.get(payload.lang.lower(), "English")
    url = f"{GLOO_BASE_URL}/ai/v2/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_gloo_token()}",
        "Content-Type": "application/json"
    }
    
    # RAG: Search the index utilizing the Topic & Scripture
    search_query = payload.topic
    if payload.scripture:
        search_query += f" {payload.scripture}"
        
    try:
        results = search_gloo(search_query, limit=8, certainty=0.45)
        snippets = extract_snippets(results)
    except Exception as e:
        logger.warning(f"Gloo search failed during sermon preparation, proceeding without context: {e}")
        snippets = []
        
    if not snippets:
        context_text = "No direct scriptural context found."
    else:
        context_text = "\n\n".join(f"- {text}" for text in snippets)
        
    system_message = (
        f"You are a highly respected homiletics professor and caring pastor. "
        f"The user needs you to build a comprehensive, structurally sound, and pastorally sensitive Sermon Prep Pack in {full_lang}.\n\n"
        f"Here is some relevant Bible scriptural text and commentary context retrieved from the search database:\n"
        f"Context:\n{context_text}\n\n"
        f"Instructions:\n"
        f"Construct a complete sermon preparation pack. The output MUST follow the exact format below, "
        f"including the specific markdown tags `# TITLE:`, `# MAIN SCRIPTURE:`, `# MEMORY VERSE:`, `# CORE THEME:`, "
        f"and the sections `## SECTION: OUTLINE`, `## SECTION: SCRIPTURES`, `## SECTION: ILLUSTRATIONS`, "
        f"`## SECTION: DISCUSSION QUESTIONS`, and `## SECTION: TEACHING NOTES`.\n"
        f"Do not deviate from these tags, as they are parsed programmatically.\n\n"
        f"Input Parameters:\n"
        f"- Topic: {payload.topic}\n"
        f"- Main Scripture: {payload.scripture if payload.scripture else 'Selected by AI'}\n"
        f"- Preaching Style: {payload.style} (Pastoral, Expository, Narrative, Theological, or Evangelistic)\n"
        f"- Duration: {payload.duration}\n"
        f"- Target Audience: {payload.audience}\n\n"
        f"Draft this pack with depth, theological integrity, and engaging pulpit relevance. Do not use placeholders.\n\n"
        f"--- \n"
        f"# TITLE: [Compelling Sermon Title]\n"
        f"# MAIN SCRIPTURE: [Primary Reference, e.g. Philippians 4:4-9]\n"
        f"# MEMORY VERSE: \"[Key memory verse, quoted]\" — [Reference]\n"
        f"# CORE THEME: [1-2 sentences summarizing the core thesis]\n\n"
        f"## SECTION: OUTLINE\n"
        f"[A structured, multi-level outline with Roman numerals I, II, III. Include detailed theological insights and practical pulpit notes.]\n\n"
        f"## SECTION: SCRIPTURES\n"
        f"### [Scripture Reference] (Supporting Verse)\n"
        f"[Full text of the verse followed by 1-2 sentences of theological context and cross-reference connection.]\n\n"
        f"### [Another Scripture Reference] (Supporting Verse)\n"
        f"[Full text and context.]\n\n"
        f"## SECTION: ILLUSTRATIONS\n"
        f"### [Illustration Name] (Illustration Badge)\n"
        f"*Story*: [A detailed, engaging story narrative, historical event, or modern analogy]\n"
        f"*Application*: [Explicit instructions on how the pastor applies this illustration to the pulpit points]\n\n"
        f"## SECTION: DISCUSSION QUESTIONS\n"
        f"Provide 5 deeply reflective small group questions:\n"
        f"1. [Question 1]\n"
        f"2. [Question 2]\n\n"
        f"## SECTION: TEACHING NOTES\n"
        f"[Write a comprehensive Small Group Guide. Include Leader Preparation notes, theological pitfalls to avoid, icebreakers, scripture reading prompts, and prayer focuses.]"
    )
    
    payload_completions = {
        "messages": [
            {"role": "system", "content": system_message},
            {
                "role": "user", 
                "content": f"Please build a full-depth, custom sermon preparation pack on: Topic: '{payload.topic}', Scripture: '{payload.scripture if payload.scripture else 'Various'}', Style: '{payload.style}', Duration: '{payload.duration}', Audience: '{payload.audience}' in {full_lang}."
            }
        ],
        "temperature": 0.7,
        "auto_routing": True
    }
    
    logger.info("Calling Gloo chat completions endpoint for Sermon Prep generation...")
    response = requests.post(url, headers=headers, json=payload_completions)
    
    if response.status_code != 200:
        logger.error(f"Gloo completions error: {response.status_code} - {response.text}")
        response.raise_for_status()
        
    answer_text = response.json()["choices"][0]["message"]["content"].strip()
    logger.info("Successfully received sermon pack text from Gloo AI completions.")
    
    parsed = parse_sermon_markdown(answer_text)
    parsed["raw_markdown"] = answer_text
    parsed["style"] = payload.style
    parsed["duration"] = payload.duration
    parsed["audience"] = payload.audience
    
    return parsed

# Endpoints
@app.get("/")
def root():
    return {"message": "SermonForge & Prayer AI API is running."}

@app.post("/prayerai-api/ark-ai")
async def prayer_ai(request: Request, payload: QueryInput):
    request_id = set_request_id(request.headers.get("x-request-id"))
    logger.info(f"Received Prayer AI Request: {payload.query}")
    try:
        result = get_prayer_and_promises(payload.query, payload.lang)
        return {"request_id": request_id, "result": result}
    except Exception as e:
        logger.exception(f"Error in Prayer AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sermonai-api/ark-ai")
async def sermon_prep_ai(request: Request, payload: SermonInput):
    request_id = set_request_id(request.headers.get("x-request-id"))
    logger.info(f"Received Sermon Prep AI Request for topic: {payload.topic}, scripture: {payload.scripture}")
    try:
        result = generate_sermon_pack(payload)
        return {"request_id": request_id, "result": result}
    except Exception as e:
        logger.exception(f"Error in Sermon Prep AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))
