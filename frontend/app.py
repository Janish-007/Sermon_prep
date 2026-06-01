import streamlit as st
import requests
import re
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SERMON_HISTORY_FILE = DATA_DIR / "sermon_history.json"

DENOMINATION_OPTIONS = [
    "General Christian",
    "Pentecostal / Charismatic",
    "Baptist / Evangelical",
    "Reformed",
    "Methodist / Wesleyan",
    "Lutheran",
    "Anglican",
    "Catholic",
    "Orthodox",
    "Non-denominational",
]

# =====================================================================
# 1. PAGE INITIALIZATION & CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="SermonForge AI | Premium Sermon Preparation Studio",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session States
if 'active_sermon' not in st.session_state:
    st.session_state.active_sermon = None
if 'history' not in st.session_state:
    try:
        if SERMON_HISTORY_FILE.exists():
            with SERMON_HISTORY_FILE.open("r", encoding="utf-8") as f:
                st.session_state.history = json.load(f)
        else:
            st.session_state.history = []
    except Exception:
        st.session_state.history = []
if 'editing_text' not in st.session_state:
    st.session_state.editing_text = ""
if 'copilot_messages' not in st.session_state:
    st.session_state.copilot_messages = []
if 'pending_sermon_update' not in st.session_state:
    st.session_state.pending_sermon_update = None

# Helper to save history persistently
def save_history_to_file():
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with SERMON_HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(st.session_state.history, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def save_copilot_chat_to_history():
    if st.session_state.active_sermon and st.session_state.history:
        for idx, hist in enumerate(st.session_state.history):
            if hist['title'] == st.session_state.active_sermon['title']:
                st.session_state.history[idx]['copilot_messages'] = st.session_state.copilot_messages
                save_history_to_file()
                break

# =====================================================================
# 2. PREMIUM CSS INJECTION (GLOO INSPIRED FAITH-AESTHETIC)
# =====================================================================
def inject_custom_styles():
    st.markdown("""
    <style>
        /* Import Elegant Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');
        
        /* General Layout Polish */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            color: #1e293b;
        }
        
        h1, h2, h3, .sermon-title-main {
            font-family: 'Playfair Display', serif;
            font-weight: 700;
        }
        
        /* Main Sidebar Branding */
        .sidebar-brand-container {
            padding: 1.5rem 1rem;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1.5rem;
        }
        .sidebar-brand-title {
            font-family: 'Playfair Display', serif;
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: 0.5px;
        }
        .sidebar-brand-subtitle {
            color: #a5b4fc;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 0.3rem;
            font-weight: 500;
        }
        
        /* Dashboard Card Widgets */
        .dashboard-header-card {
            background: linear-gradient(135deg, #1e1b4b, #312e81);
            color: white;
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(30, 27, 75, 0.2);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(165, 180, 252, 0.2);
        }
        .dashboard-header-card::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(217, 119, 6, 0.15) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        .dashboard-category {
            color: #fbbf24;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        .dashboard-title {
            font-size: 2.6rem;
            margin: 0.5rem 0;
            font-family: 'Playfair Display', serif;
            line-height: 1.2;
        }
        .dashboard-subtitle {
            color: #cbd5e1;
            font-size: 1.1rem;
            font-weight: 300;
            max-width: 800px;
            margin-top: 0.5rem;
            line-height: 1.6;
        }
        
        /* Grid Layout Cards */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 1.25rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
            border-color: #cbd5e1;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.25rem;
        }
        .stat-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1e1b4b;
        }
        
        /* Scripture quote panels */
        .scripture-quote-container {
            background-color: #f8fafc;
            border-left: 4px solid #d97706; /* Gold vertical bar */
            padding: 1.5rem;
            border-radius: 0 12px 12px 0;
            margin: 1.5rem 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);
        }
        .scripture-text {
            font-family: 'Playfair Display', serif;
            font-size: 1.25rem;
            font-style: italic;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 0.75rem;
        }
        .scripture-reference {
            font-weight: 600;
            color: #0f172a;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Premium Card styling for Illustrations and Small Group Pack */
        .premium-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .premium-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(to bottom, #4f46e5, #d97706);
        }
        .premium-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -5px rgba(0, 0, 0, 0.05);
        }
        .card-header-badge {
            background-color: rgba(79, 70, 229, 0.1);
            color: #4f46e5;
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
            margin-bottom: 1rem;
        }
        .card-title {
            font-size: 1.4rem;
            color: #0f172a;
            margin-bottom: 1rem;
            font-family: 'Playfair Display', serif;
            font-weight: 600;
        }
        
        /* Custom Button Styling */
        .stButton>button {
            background: linear-gradient(135deg, #4f46e5, #4338ca) !important;
            color: white !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 0.6rem 1.8rem !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2) !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 12px rgba(79, 70, 229, 0.3) !important;
            background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        }
        
        /* Welcome Panel Style */
        .welcome-container {
            text-align: center;
            max-width: 750px;
            margin: 3rem auto;
            padding: 3rem;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 24px;
            border: 1px solid rgba(226, 232, 240, 0.8);
            box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.05);
            backdrop-filter: blur(10px);
        }
        .welcome-icon {
            font-size: 3.5rem;
            background: linear-gradient(135deg, #4f46e5, #d97706);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1.5rem;
            display: inline-block;
        }
        .welcome-title {
            font-size: 2.2rem;
            margin-bottom: 1rem;
            color: #0f172a;
        }
        .welcome-text {
            color: #475569;
            font-size: 1.1rem;
            line-height: 1.7;
            margin-bottom: 2rem;
        }
        .gloo-philosophy-card {
            background-color: #fafaf9;
            border: 1px solid #f5f5f4;
            border-radius: 12px;
            padding: 1.25rem;
            font-size: 0.85rem;
            color: #78716c;
            line-height: 1.5;
            text-align: left;
            margin-top: 1.5rem;
            border-left: 3px solid #d97706;
        }
    </style>
    """, unsafe_allow_html=True)

# Run Styles
inject_custom_styles()

# =====================================================================
# 4. PARSER HELPER FOR AI OUTPUT (FALLBACK IN CASE BACKEND RETURNS STR)
# =====================================================================
def parse_sermon_markdown(text):
    """Fallback client-side parser to translate markdown to UI dict if needed."""
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
                
                role = "Cross Reference"
                role_match = re.search(r"\(([^)]+)\)", ref_line)
                if role_match:
                    role = role_match.group(1)
                    ref_line = re.sub(r"\([^)]+\)", "", ref_line).strip()
                    
                result["scriptures"].append({"ref": ref_line, "text": text_line, "role": role})
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
                
                badge = "Illustration"
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

# =====================================================================
# 5. PDF GENERATION UTILITY (FPDF2)
# =====================================================================
def clean_for_pdf(txt):
    if not txt:
        return ""
    replacements = {
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '—': '-', '–': '-', '…': '...', '•': '-',
        '\u2013': '-', '\u2014': '-', '\u2018': "'",
        '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2022': '-', '\u2026': '...'
    }
    for orig, rep in replacements.items():
        txt = txt.replace(orig, rep)
    return txt.encode('latin-1', 'replace').decode('latin-1')

def generate_sermon_pdf(sermon_data):
    from fpdf import FPDF
    
    class SermonPDF(FPDF):
        def header(self):
            if self.page_no() > 1:
                self.set_font('helvetica', 'I', 8)
                self.set_text_color(100, 116, 139)
                self.cell(0, 10, clean_for_pdf(sermon_data["title"]), 0, 0, 'R')
                self.ln(10)
                self.set_draw_color(226, 232, 240)
                self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
                self.ln(5)
                
        def footer(self):
            self.set_y(-15)
            self.set_draw_color(226, 232, 240)
            self.line(10, self.get_y(), 200, self.get_y())
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 10, 'SermonForge AI  |  Prepared via Gloo Native RAG', 0, 0, 'L')
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')

    pdf = SermonPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # ------------------ COVER PAGE / MAIN HEADER ------------------
    pdf.set_fill_color(30, 27, 75)
    pdf.rect(0, 0, 210, 65, 'F')
    
    pdf.set_xy(15, 15)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(251, 191, 36)
    pdf.cell(0, 5, 'SERMON PREPARATION PACK  |  GLOO NATIVE RAG', 0, 1, 'L')
    
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(180, 8, clean_for_pdf(sermon_data["title"]))
    
    pdf.ln(3)
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 5, f"Style: {sermon_data.get('style', 'Theological')}   |   Duration: {sermon_data.get('duration', '30m')}   |   Audience: {sermon_data.get('audience', 'General')}", 0, 1, 'L')
    pdf.cell(0, 5, f"Denomination: {sermon_data.get('denomination', 'General Christian')}", 0, 1, 'L')
    
    # Rest of document layout
    pdf.set_xy(10, 75)
    pdf.set_text_color(30, 41, 59)
    
    # 1. Memory Verse Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(217, 119, 6)
    pdf.rect(15, 75, 180, 28, 'FD')
    
    pdf.set_xy(18, 77)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_text_color(217, 119, 6)
    pdf.cell(0, 5, 'MEMORY VERSE', 0, 1, 'L')
    pdf.set_x(18)
    pdf.set_font('helvetica', 'I', 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(174, 5, clean_for_pdf(sermon_data["memory_verse"]))
    
    # 2. Core Theme
    pdf.set_xy(15, 110)
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 6, 'CORE THEOLOGICAL THESIS', 0, 1, 'L')
    pdf.line(15, 117, 195, 117)
    pdf.ln(3)
    pdf.set_x(15)
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(180, 5, clean_for_pdf(sermon_data["theme"]))
    
    # 3. Outline
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, 'I. HOMILETICAL SERMON OUTLINE', 0, 1, 'L')
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(30, 41, 59)
    outline_lines = sermon_data["outline"].split("\n")
    for line in outline_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("###"):
            pdf.ln(3)
            pdf.set_font('helvetica', 'B', 11)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(180, 5, clean_for_pdf(line.replace("###", "").strip()))
            pdf.set_font('helvetica', '', 10)
            pdf.set_text_color(30, 41, 59)
        elif line.startswith("*") or line.startswith("-"):
            pdf.set_x(20)
            pdf.multi_cell(175, 5, "- " + clean_for_pdf(line.lstrip("* -").strip()))
        else:
            pdf.set_x(15)
            pdf.multi_cell(180, 5, clean_for_pdf(line))
            
    # 4. Scripture Vault
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, 'II. SCRIPTURE VAULT', 0, 1, 'L')
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    if sermon_data.get("scriptures"):
        for scr in sermon_data["scriptures"]:
            pdf.set_font('helvetica', 'B', 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, clean_for_pdf(f"{scr['ref']} - {scr['role']}"), 0, 1, 'L')
            pdf.set_font('helvetica', 'I', 10)
            pdf.set_text_color(71, 85, 105)
            pdf.multi_cell(180, 5, clean_for_pdf(scr["text"]))
            pdf.ln(4)
    else:
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(180, 5, clean_for_pdf(sermon_data.get("scriptures_raw", "")))
        
    # 5. Illustrations
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, 'III. HOMILETICAL ILLUSTRATIONS', 0, 1, 'L')
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    if sermon_data.get("illustrations"):
        for ill in sermon_data["illustrations"]:
            pdf.set_font('helvetica', 'B', 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, clean_for_pdf(f"{ill['title']} ({ill['badge']})"), 0, 1, 'L')
            pdf.set_font('helvetica', '', 10)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(18)
            pdf.multi_cell(177, 5, "Story: " + clean_for_pdf(ill["story"]))
            pdf.set_x(18)
            pdf.set_font('helvetica', 'B', 9)
            pdf.cell(30, 5, "Pulpit Application: ", 0, 0, 'L')
            pdf.set_font('helvetica', 'I', 9)
            pdf.multi_cell(147, 5, clean_for_pdf(ill["application"]))
            pdf.ln(5)
    else:
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(180, 5, clean_for_pdf(sermon_data.get("illustrations_raw", "")))

    # 6. Discussion Questions
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, 'IV. DISCIPLESHIP DISCUSSION QUESTIONS', 0, 1, 'L')
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    if sermon_data.get("discussion_questions"):
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(30, 41, 59)
        for i, q in enumerate(sermon_data["discussion_questions"], 1):
            pdf.multi_cell(180, 5, f"{i}. {clean_for_pdf(q)}")
            pdf.ln(2)
    else:
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(180, 5, clean_for_pdf(sermon_data.get("questions_raw", "")))

    # 7. Teaching Notes
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(79, 70, 229)
    pdf.cell(0, 8, 'V. SMALL GROUP TEACHING NOTES', 0, 1, 'L')
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(180, 5, clean_for_pdf(sermon_data["teaching_notes"]))

    return pdf.output()

# =====================================================================
# 6. STREAMLIT APP LAYOUT & SIDEBAR
# =====================================================================

# --- Sidebar Header and Branding ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-container">
        <h1 class="sidebar-brand-title">SermonForge AI</h1>
        <div class="sidebar-brand-subtitle">Gloo Native RAG Ecosystem</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🛠️ Setup & Options")
    
    local_api_url = "http://127.0.0.1:8000/sermonai-api/ark-ai"
    
    # Input Selection
    st.subheader("💡 Prep Pack Details")
    
    live_topic = st.text_area(
        "Sermon Topic, Scripture, or Theme", 
        placeholder="e.g. Grace that Restores (Luke 15), Finding Peace in Anxiety, Purpose...",
        height=120,
        help="Type in a biblical topic, a scripture passage, or a message theme."
    )

    live_denomination = st.selectbox(
        "Denomination Category",
        options=DENOMINATION_OPTIONS,
        index=0,
        help="Shapes theological emphasis, vocabulary, illustrations, and ministry application."
    )
    
    # Hidden advanced options
    with st.expander("⚙️ Advanced Settings"):
        live_style = st.selectbox(
            "Sermon Style",
            options=["Pastoral", "Expository", "Narrative", "Theological", "Evangelistic"],
            index=0,
            help="Preaching style direction."
        )
        live_dur = st.selectbox(
            "Target Duration",
            options=["15 mins", "30 mins", "45 mins"],
            index=1
        )
        live_aud = st.selectbox(
            "Target Audience",
            options=["General Congregation", "Youth / Young Adults", "Midweek Fellowship", "Seeker / Outreach"],
            index=0
        )
        live_lang = st.selectbox(
            "Language",
            options=["en", "ta"],
            format_func=lambda x: "English" if x == "en" else "Tamil",
            index=0
        )

    st.write("")
    
    if st.button("🔥 Build Sermon Pack", use_container_width=True):
        if not live_topic:
            st.error("Please enter a Topic or Theme to begin generation!")
        else:
            with st.spinner("Connecting to Gloo AI RAG Backend... (Takes 10-15s)"):
                payload = {
                    "topic": live_topic,
                    "style": live_style,
                    "duration": live_dur,
                    "audience": live_aud,
                    "denomination": live_denomination,
                    "lang": live_lang
                }
                
                try:
                    response = requests.post(local_api_url, json=payload, timeout=40)
                    if response.status_code == 200:
                        api_out = response.json().get("result", {})
                        st.session_state.active_sermon = api_out
                        st.session_state.editing_text = api_out.get("raw_markdown", "")
                        st.session_state.copilot_messages = []
                        st.session_state.pending_sermon_update = None
                        
                        # Add to history
                        st.session_state.history.append({
                            "title": api_out.get("title", live_topic),
                            "style": live_style,
                            "duration": api_out.get("duration", live_dur),
                            "audience": api_out.get("audience", live_aud),
                            "denomination": api_out.get("denomination", live_denomination),
                            "raw_markdown": api_out.get("raw_markdown", ""),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "copilot_messages": []
                        })
                        save_history_to_file()
                        st.success("Sermon Prep Pack Constructed Successfully!")
                        st.rerun()
                    else:
                        st.error(f"Backend Server Error ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Failed to communicate with FastAPI backend server: {str(e)}")
                    st.info("💡 Double check that your FastAPI uvicorn terminal is running and contains valid Gloo credentials in the `.env` file!")

    st.divider()
    
    # History Sidebar
    st.subheader("📚 Saved Prep Archives")
    if st.session_state.history:
        for idx, hist in enumerate(reversed(st.session_state.history)):
            hist_col, del_col = st.columns([5, 1])
            with hist_col:
                if st.button(f"📖 {hist['title'][:25]}...", key=f"hist_{idx}", use_container_width=True):
                    parsed = parse_sermon_markdown(hist['raw_markdown'])
                    parsed['style'] = hist.get('style', 'Theological')
                    parsed['duration'] = hist.get('duration', '30 mins')
                    parsed['audience'] = hist.get('audience', 'General Congregation')
                    parsed['denomination'] = hist.get('denomination', 'General Christian')
                    parsed['raw_markdown'] = hist['raw_markdown']
                    
                    st.session_state.active_sermon = parsed
                    st.session_state.editing_text = hist['raw_markdown']
                    st.session_state.copilot_messages = hist.get('copilot_messages', [])
                    st.session_state.pending_sermon_update = None
                    st.success(f"Restored: {parsed['title']}")
                    st.rerun()
            with del_col:
                if st.button("❌", key=f"del_{idx}"):
                    actual_idx = len(st.session_state.history) - 1 - idx
                    removed = st.session_state.history.pop(actual_idx)
                    save_history_to_file()
                    st.toast(f"Deleted: {removed['title']}")
                    st.rerun()
    else:
        st.caption("No previously generated sermons. Use the options above to build your first pack!")

# --- Main App Layout ---
st.title("⛪ SermonForge AI Prep Studio")
st.caption("Integrated on Gloo Native RAG Platform to construct scripture-grounded sermon prep archives.")
st.divider()

if st.session_state.active_sermon is None:
    # --- Landing / Welcome Dashboard ---
    st.markdown(f"""
    <div class="welcome-container">
        <div class="welcome-icon">⛪</div>
        <h2 class="welcome-title">Welcome to SermonForge AI</h2>
        <p class="welcome-text">
            SermonForge AI acts as your dedicated theological study assistant, handling the structural groundwork of sermon preparation. 
            By compiling outlines, scripture cross-references, illustrations, and group materials, it saves hours of organization time, 
            allowing you to focus on study, prayer, and deep spiritual alignment.
        </p>
        <div class="stat-grid" style="margin-top: 2rem;">
            <div class="stat-card">
                <div class="stat-label">✨ Rapid Outlines</div>
                <div class="stat-value" style="font-size: 0.95rem; color: #4f46e5; margin-top:0.3rem;">Structured Homiletical Flow</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📖 Scripture Vault</div>
                <div class="stat-value" style="font-size: 0.95rem; color: #4f46e5; margin-top:0.3rem;">Gloo Bible RAG Integration</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">💡 Pulpit Stories</div>
                <div class="stat-value" style="font-size: 0.95rem; color: #4f46e5; margin-top:0.3rem;">Modern & Historical Analogies</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">👥 Group Notes</div>
                <div class="stat-value" style="font-size: 0.95rem; color: #4f46e5; margin-top:0.3rem;">Discussion Guides & Cues</div>
            </div>
        </div>
        <div class="gloo-philosophy-card">
            <strong>Gloo AI Ministry Philosophy:</strong> 
            "The pastor brings the anointing and the personalized message — our AI handles the groundwork. 
            We build tools that align with biblical truth and honor the spiritual weight of your office."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("👈 Input your sermon topic, scripture passage, or theme in the sidebar, and click **Build Sermon Pack** to begin!")

else:
    # --- Active Sermon Dashboard & Tabs ---
    sermon = st.session_state.active_sermon
    
    # Header Card
    st.markdown(f"""
    <div class="dashboard-header-card">
        <div class="dashboard-category">{sermon.get('style', 'General')} Study  •  {sermon.get('duration', '30m')}  •  {sermon.get('audience', 'General')}  •  {sermon.get('denomination', 'General Christian')}</div>
        <h1 class="dashboard-title">{sermon["title"]}</h1>
        <p class="dashboard-subtitle"><strong>Core Theme:</strong> {sermon["theme"]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick metadata columns
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Primary Text</div>
            <div class="stat-value">{sermon["main_scripture"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with stat2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Preparation Level</div>
            <div class="stat-value" style="color: #059669;">Ready for Pulpit</div>
        </div>
        """, unsafe_allow_html=True)
    with stat3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Denomination</div>
            <div class="stat-value">{sermon.get('denomination', 'General Christian')}</div>
        </div>
        """, unsafe_allow_html=True)
    with stat4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">System Mode</div>
            <div class="stat-value" style="color: #4f46e5;">Gloo Native RAG</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # Actions for downloads
    act_col1, act_col2, act_col3 = st.columns([6, 2, 2])
    with act_col1:
        st.write("")
    with act_col2:
        # Download raw markdown file
        st.download_button(
            label="💾 Download Markdown (.md)",
            data=st.session_state.editing_text,
            file_name=f"{sermon['title'].lower().replace(' ', '_')}_pack.md",
            mime="text/markdown",
            use_container_width=True
        )
    with act_col3:
        # Download FPDF2 PDF
        try:
            pdf_bytes = generate_sermon_pdf(sermon)
            st.download_button(
                label="🖨️ Download Print PDF",
                data=pdf_bytes,
                file_name=f"{sermon['title'].lower().replace(' ', '_')}_pack.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as pdf_ex:
            st.button("⚠️ PDF Export Unavailable", disabled=True, use_container_width=True, help=f"PDF Error: {str(pdf_ex)}")

    st.write("")

    # Tab Container
    tab_overview, tab_outline, tab_scripture, tab_illustrations, tab_group, tab_editor, tab_copilot = st.tabs([
        "📋 Overview", 
        "📝 Homiletical Outline", 
        "📖 Scripture Vault", 
        "💡 Pulpit Illustrations", 
        "👥 Small Group Pack", 
        "✍️ Manuscript & Workspace",
        "💬 Sermon AI Copilot"
    ])
    
    # 1. OVERVIEW TAB
    with tab_overview:
        st.subheader("Sermon Pack Dashboard")
        st.markdown(f"""
        <div class="scripture-quote-container">
            <div class="scripture-text">{sermon["memory_verse"]}</div>
            <div class="scripture-reference">Selected Memory Scripture</div>
        </div>
        """, unsafe_allow_html=True)
        
        col_theme, col_notes = st.columns(2)
        with col_theme:
            st.info("### 🕊️ Preaching Direction")
            st.write(f"This sermon is configured in an **{sermon.get('style', 'Pastoral')}** style for a **{sermon.get('denomination', 'General Christian')}** context, targeting an audience of **{sermon.get('audience', 'General')}** over **{sermon.get('duration', '30 mins')}**.")
            st.write("Our homiletical structures optimize for theological precision while leaving space for personal, pastoral applications.")
            
        with col_notes:
            st.success("### 🚀 Dynamic Activation")
            st.write("All generated components are saved and available for editing in the workspace tab. Click the editor tab above to add personal study comments, direct manuscript notes, and tailored adjustments before exporting to PDF.")

    # 2. OUTLINE TAB
    with tab_outline:
        st.subheader("Homiletical Outline")
        st.caption("A logical, biblical structure designed for preaching flow. Edit these points in the workspace tab.")
        
        # Render outline
        outline_parts = sermon["outline"].split("###")
        for part in outline_parts:
            part = part.strip()
            if not part:
                continue
            lines = part.split("\n")
            header = lines[0].strip()
            bullets = "\n".join(lines[1:]).strip()
            
            st.markdown(f"#### 🏷️ {header}")
            st.markdown(bullets)
            st.divider()

    # 3. SCRIPTURE VAULT TAB
    with tab_scripture:
        st.subheader("Scripture Vault")
        st.caption("Primary text and contextual cross-references for sermon depth, retrieved using Gloo vector search.")
        
        if sermon["scriptures"]:
            for scr in sermon["scriptures"]:
                st.markdown(f"""
                <div class="scripture-quote-container">
                    <div class="scripture-reference">{scr["ref"]}  ({scr["role"]})</div>
                    <div class="scripture-text" style="font-size: 1.1rem; margin-top: 0.5rem; color: #475569;">{scr["text"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write(sermon.get("scriptures_raw", "No scripture details found."))

    # 4. ILLUSTRATIONS TAB
    with tab_illustrations:
        st.subheader("Homiletical Illustrations")
        st.caption("Engaging, modern, or historical stories to connect the pulpit to the congregation's daily life.")
        
        if sermon["illustrations"]:
            for ill in sermon["illustrations"]:
                st.markdown(f"""
                <div class="premium-card">
                    <div class="card-header-badge">{ill["badge"]}</div>
                    <div class="card-title">{ill["title"]}</div>
                    <p style="font-size: 1rem; color: #334155; line-height: 1.6;"><strong>Story / Analogy:</strong><br>{ill["story"]}</p>
                    <p style="font-size: 0.95rem; font-style: italic; color: #b45309; background-color: #fef3c7; padding: 0.8rem; border-radius: 8px; margin-top: 1rem;">
                        <strong>Pulpit Application:</strong> {ill["application"]}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write(sermon.get("illustrations_raw", "No illustration details found."))

    # 5. SMALL GROUP PACK TAB
    with tab_group:
        st.subheader("Disciple small group Pack")
        st.caption("Comprehensive discussion questions and leader notes to distribute to home fellowships.")
        
        st.markdown("### 💬 Discipleship Discussion Questions")
        if sermon["discussion_questions"]:
            for i, q in enumerate(sermon["discussion_questions"], 1):
                st.markdown(f"""
                <div style="background-color: #f8fafc; color: #1e293b; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; margin-bottom: 0.75rem;">
                    <strong>Question {i}:</strong> {q}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write(sermon.get("questions_raw", "No discussion questions found."))
            
        st.divider()
        st.markdown("### 📋 Leader Teaching Notes")
        st.markdown(sermon["teaching_notes"])

    # 6. WORKSPACE EDITOR TAB
    with tab_editor:
        st.subheader("Sermon Workspace & Editor")
        st.caption("Refine the generated material, write your full message manuscript, or paste additional verses.")
        
        # Text Area Editor
        updated_text = st.text_area(
            "Active Sermon Pack Markdown",
            value=st.session_state.editing_text,
            height=500,
            help="Directly edit the markdown structure. Changes will be reflected in the Download and PDF output files."
        )
        
        # Save edits
        if st.button("💾 Apply & Save Edits", use_container_width=True):
            st.session_state.editing_text = updated_text
            parsed_edits = parse_sermon_markdown(updated_text)
            parsed_edits['style'] = sermon.get('style', 'Pastoral')
            parsed_edits['duration'] = sermon.get('duration', '30 mins')
            parsed_edits['audience'] = sermon.get('audience', 'General Congregation')
            parsed_edits['denomination'] = sermon.get('denomination', 'General Christian')
            parsed_edits['raw_markdown'] = updated_text
            
            st.session_state.active_sermon = parsed_edits
            
            # Find in history and update
            for idx, hist in enumerate(st.session_state.history):
                if hist['title'] == sermon['title']:
                    st.session_state.history[idx]['raw_markdown'] = updated_text
                    st.session_state.history[idx]['denomination'] = sermon.get('denomination', 'General Christian')
                    save_history_to_file()
                    break
                    
            st.success("Sermon Workspace Updated and Saved Locally!")
            st.rerun()
            
        st.caption("💡 **Tip:** Standard Markdown syntax is fully supported. Use `#` for major headings, `*` for bullet points, and `**` for bold highlights.")

    # 7. WORKSPACE COPILOT TAB
    with tab_copilot:
        st.subheader("💬 Sermon AI Copilot")
        st.caption("Brainstorm ideas, add illustrations, ask theological questions, or direct the AI to rewrite sections of your sermon.")
        
        copilot_api_url = "http://127.0.0.1:8000/sermonai-api/copilot"

        # Check if we have a pending sermon pack update suggested by the Copilot
        if st.session_state.pending_sermon_update:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); border: 1px solid #16a34a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.1);">
                <h4 style="color: #14532d; margin: 0 0 0.5rem 0; font-family: 'Outfit', sans-serif;">✨ Copilot Suggested a Sermon Update!</h4>
                <p style="color: #166534; font-size: 0.95rem; margin-bottom: 1rem;">
                    The Copilot has generated an adjusted draft based on your request. You can preview this outline revision or apply it to replace your active study workspace.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            up_col1, up_col2 = st.columns(2)
            with up_col1:
                if st.button("🚀 Apply Copilot Refinements", use_container_width=True):
                    # Apply changes to active workspace
                    new_markdown = st.session_state.pending_sermon_update
                    parsed_update = parse_sermon_markdown(new_markdown)
                    parsed_update['style'] = sermon.get('style', 'Pastoral')
                    parsed_update['duration'] = sermon.get('duration', '30 mins')
                    parsed_update['audience'] = sermon.get('audience', 'General Congregation')
                    parsed_update['denomination'] = sermon.get('denomination', 'General Christian')
                    parsed_update['raw_markdown'] = new_markdown
                    
                    st.session_state.active_sermon = parsed_update
                    st.session_state.editing_text = new_markdown
                    
                    # Update active history record
                    for idx, hist in enumerate(st.session_state.history):
                        if hist['title'] == sermon['title']:
                            st.session_state.history[idx]['raw_markdown'] = new_markdown
                            break
                    
                    st.session_state.pending_sermon_update = None
                    save_history_to_file()
                    st.success("Sermon Workspace and tabs updated successfully with Copilot adjustments!")
                    st.rerun()
            with up_col2:
                if st.button("❌ Discard Draft", use_container_width=True):
                    st.session_state.pending_sermon_update = None
                    st.toast("Discarded copilot's revised sermon draft.")
                    st.rerun()
            st.divider()

        # Display Chat History
        chat_container = st.container()
        with chat_container:
            if st.session_state.copilot_messages:
                for msg in st.session_state.copilot_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            else:
                st.markdown(f"""
                <div style="text-align: center; color: #64748b; padding: 3rem 1rem;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">💬</div>
                    <h5>SermonForge Homiletical Dialogue</h5>
                    <p style="font-size: 0.9rem; max-width: 500px; margin: 0 auto;">
                        Ask your homiletical copilot to brainstorm alternative hooks, suggest scripture references, draft detailed leader guides, or edit the active outline!
                    </p>
                    <div style="display: flex; gap: 0.5rem; justify-content: center; margin-top: 1.5rem; flex-wrap: wrap;">
                        <span style="background-color: #f1f5f9; padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.8rem; border: 1px solid #e2e8f0; color: #475569;">"Suggest a story illustration about forgiveness"</span>
                        <span style="background-color: #f1f5f9; padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.8rem; border: 1px solid #e2e8f0; color: #475569;">"Make outline point II more expository"</span>
                        <span style="background-color: #f1f5f9; padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.8rem; border: 1px solid #e2e8f0; color: #475569;">"Add scripture cross-references for Romans 8"</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Chat Input at the bottom
        if user_prompt := st.chat_input("Tell Copilot how to refine your sermon..."):
            # Append User message to local state
            st.session_state.copilot_messages.append({"role": "user", "content": user_prompt})
            save_copilot_chat_to_history()
            
            with st.chat_message("user"):
                st.markdown(user_prompt)
                
            # Call Copilot API
            with st.spinner("Copilot is drafting homiletical insights..."):
                payload = {
                    "messages": st.session_state.copilot_messages,
                    "active_sermon_markdown": st.session_state.editing_text,
                    "denomination": sermon.get('denomination', 'General Christian'),
                    "style": sermon.get('style', 'Pastoral'),
                    "lang": live_lang if 'live_lang' in locals() else 'en'
                }
                
                try:
                    copilot_response = requests.post(copilot_api_url, json=payload, timeout=50)
                    if copilot_response.status_code == 200:
                        res_data = copilot_response.json().get("result", {})
                        bot_response = res_data.get("chat_response", "")
                        updated_sermon_md = res_data.get("updated_sermon")
                        
                        # Append Assistant message to state
                        st.session_state.copilot_messages.append({"role": "assistant", "content": bot_response})
                        
                        if updated_sermon_md:
                            st.session_state.pending_sermon_update = updated_sermon_md
                            
                        save_copilot_chat_to_history()
                        st.rerun()
                    else:
                        st.error(f"Copilot API Error ({copilot_response.status_code}): {copilot_response.text}")
                except Exception as ex:
                    st.error(f"Failed to communicate with Copilot backend: {str(ex)}")

