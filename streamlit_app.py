import streamlit as st
import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="SaarthiAI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    border-right: 1px solid rgba(255,255,255,0.1);
}

.node-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 12px 0;
    transition: all 0.3s ease;
    position: relative;
}

.node-card.active {
    border-color: #6c63ff;
    box-shadow: 0 0 24px rgba(108,99,255,0.35);
    background: rgba(108,99,255,0.12);
}

.node-card.completed {
    border-color: #00d4aa;
    background: rgba(0,212,170,0.08);
}

.node-card.error {
    border-color: #ff6b6b;
    background: rgba(255,107,107,0.08);
}

.node-connector {
    width: 2px;
    height: 28px;
    background: linear-gradient(to bottom, rgba(108,99,255,0.6), rgba(108,99,255,0.15));
    margin: 0 auto;
}

.stage-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.badge-pending { background: rgba(255,255,255,0.1); color: #aaa; }
.badge-active { background: rgba(108,99,255,0.3); color: #b8b0ff; }
.badge-completed { background: rgba(0,212,170,0.2); color: #00d4aa; }
.badge-error { background: rgba(255,107,107,0.2); color: #ff9999; }

.compliance-pill {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    margin: 4px;
}
.pill-ok { background: rgba(0,212,170,0.2); color: #00d4aa; border: 1px solid rgba(0,212,170,0.4); }
.pill-review { background: rgba(255,193,7,0.2); color: #ffc107; border: 1px solid rgba(255,193,7,0.4); }
.pill-fail { background: rgba(255,107,107,0.2); color: #ff6b6b; border: 1px solid rgba(255,107,107,0.4); }

h1, h2, h3, h4, h5 { color: #ffffff !important; }
p, label, .stMarkdown { color: #d0d0e0 !important; }

.stButton button {
    background: linear-gradient(135deg, #6c63ff, #a78bfa);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(108,99,255,0.4);
}

.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

API_BASE = "http://127.0.0.1:8000"

def render_node(title, icon, status, description=None, content=None):
    cls = f"node-card {status}"
    badge_cls = f"badge-{status}"
    status_labels = {"pending": "Pending", "active": "Processing...", "completed": "Complete", "error": "Error"}
    badge_label = status_labels.get(status, status.title())
    desc_html = f"<p style='color:#aaa;font-size:13px;margin:4px 0 0;'>{description}</p>" if description else ""
    content_html = f"<div style='margin-top:12px;'>{content}</div>" if content else ""
    st.markdown(f"""
    <div class="{cls}">
        <span class="stage-badge {badge_cls}">{badge_label}</span>
        <h4 style="margin:0;font-size:17px;">{icon} {title}</h4>
        {desc_html}
        {content_html}
    </div>
    """, unsafe_allow_html=True)

def connector():
    st.markdown('<div class="node-connector"></div>', unsafe_allow_html=True)

async def get_requirements_api():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{API_BASE}/api/v1/requirements", timeout=5.0)
        return r.json() if r.status_code == 200 else []

async def get_document_types_api():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{API_BASE}/api/v1/document-types", timeout=5.0)
        return r.json() if r.status_code == 200 else []

async def get_requirements_by_type_api(doc_type_id: int):
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{API_BASE}/api/v1/requirements/by-type/{doc_type_id}", timeout=5.0)
        return r.json() if r.status_code == 200 else []

async def add_document_type_api(payload):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API_BASE}/api/v1/document-types", json=payload, timeout=10.0)
        return r.status_code in (200, 201)

async def delete_document_type_api(dt_id: int):
    async with httpx.AsyncClient() as c:
        r = await c.delete(f"{API_BASE}/api/v1/document-types/{dt_id}", timeout=10.0)
        return r.status_code == 200

async def submit_document_request(aadhar_number, document_request_type):
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f"{API_BASE}/api/v1/submit",
            json={"aadhar_number": aadhar_number, "document_request_type": document_request_type})
        return r.json() if r.status_code == 200 else {"error": r.text, "status": "error"}

async def add_requirement_api(payload):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API_BASE}/api/v1/requirements", json=payload, timeout=10.0)
        return r.status_code in (200, 201)

async def delete_requirement_api(req_id):
    async with httpx.AsyncClient() as c:
        r = await c.delete(f"{API_BASE}/api/v1/requirements/{req_id}", timeout=10.0)
        return r.status_code == 200

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except Exception:
        return asyncio.run(coro)

def citizen_page():
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<h1 style='text-align:center;font-size:36px;'>🏛️ SaarthiAI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#9090bb;font-size:15px;margin-bottom:32px;'>Government Document Processing Portal</p>", unsafe_allow_html=True)

        doc_types = run_async(get_document_types_api())
        if not doc_types:
            st.warning("No document types available. Please ask the admin to configure them.")
            return

        dt_options = {dt["name"]: dt for dt in doc_types}

        with st.form("submit_form"):
            aadhar = st.text_input("Aadhar Number", placeholder="12-digit Aadhar number", max_chars=12)
            selected_dt_name = st.selectbox("Document Request Type", list(dt_options.keys()))
            submitted = st.form_submit_button("🔍 Check Requirements")

        if submitted and aadhar:
            if len(aadhar) != 12 or not aadhar.isdigit():
                st.error("Please enter a valid 12-digit Aadhar number.")
            else:
                selected_dt = dt_options[selected_dt_name]
                st.session_state["aadhar_number"] = aadhar
                st.session_state["doc_type"] = selected_dt["slug"]
                st.session_state["doc_type_id"] = selected_dt["id"]
                st.session_state["doc_type_label"] = selected_dt_name
                requirements = run_async(get_requirements_by_type_api(selected_dt["id"]))
                st.session_state["requirements"] = requirements
                st.session_state["stage"] = "upload"


        if st.session_state.get("stage") == "upload":
            requirements = st.session_state.get("requirements", [])
            doc_type_label = st.session_state.get("doc_type_label") or st.session_state.get("doc_type", "")
            st.markdown("---")

            render_node("Identity Verified", "✅", "completed",
                f"Aadhar: {st.session_state.get('aadhar_number')} · {doc_type_label}")
            connector()

            st.markdown("""<div class="node-card active">
                <span class="stage-badge badge-active">Upload Documents</span>
                <h4 style="margin:0;font-size:17px;">📁 Document Uploads</h4>
                <p style='color:#aaa;font-size:13px;'>Upload the required files for this request type</p>
            </div>""", unsafe_allow_html=True)

            if requirements:
                for req in requirements:
                    st.file_uploader(
                        f"{'🔴' if req.get('is_mandatory') else '🟡'} {req['name']}",
                        key=f"upload_{req['id']}",
                        help=req.get("description", "")
                    )
            else:
                st.info(f"No configured requirements found for doc type '{doc_type_label}'. Add from the Admin Panel.")

            connector()
            render_node("Vault Analysis", "🔍", "pending", "Tesseract OCR & Gemini Vision")
            connector()
            render_node("Compliance Assessment", "⚖️", "pending", "RAG policy cross-check")
            connector()
            render_node("Tracking Created", "📌", "pending", "Status set to in_review")

            if st.button("🚀 Submit Request", use_container_width=True):
                with st.spinner("Processing your document request..."):
                    result = run_async(submit_document_request(
                        st.session_state["aadhar_number"],
                        st.session_state["doc_type"]
                    ))
                st.session_state["result"] = result
                st.session_state["stage"] = "result"
                st.rerun()

        if st.session_state.get("stage") == "result":
            result = st.session_state.get("result", {})
            has_error = "error" in result
            st.markdown("---")

            render_node("Identity Verified", "✅", "completed")
            connector()
            render_node("Document Upload", "📁", "completed")
            connector()
            render_node("Vault Analysis", "🔍", "completed")
            connector()
            render_node("Compliance Assessment", "⚖️", "completed")
            connector()

            if has_error:
                render_node("Request Failed", "❌", "error",
                    content=f"<p style='color:#ff9999;'>{result.get('error', 'Unknown error')}</p>")
            else:
                tracking_id = result.get("tracking_id")
                render_node(
                    f"Request Submitted — Tracking #{tracking_id}", "📌", "completed",
                    content=f"<p style='color:#aaa;'>{result.get('message', '')}</p>"
                )

            compliance = result.get("compliance_report", {})
            if compliance:
                st.markdown("### ⚖️ Compliance Report")
                for req_name, assessment in compliance.items():
                    s = assessment.get("status", "review_needed")
                    pill_cls = "pill-ok" if s == "compliant" else ("pill-fail" if s == "non_compliant" else "pill-review")
                    icon = "✅" if s == "compliant" else ("❌" if s == "non_compliant" else "⚠️")
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;margin:8px 0;">
                        <span class="compliance-pill {pill_cls}">{icon} {s.replace('_',' ').title()}</span>
                        <strong style="color:white;"> {req_name}</strong>
                        <p style="color:#aaa;margin:8px 0 0;font-size:13px;">{assessment.get('notes', '')}</p>
                    </div>""", unsafe_allow_html=True)

            if st.button("🔄 New Request"):
                for k in ["stage", "result", "requirements", "aadhar_number", "doc_type"]:
                    st.session_state.pop(k, None)
                st.rerun()


def admin_page():
    st.markdown("<h1>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9090bb;'>Manage document types and their requirements</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📁 Document Types", "📋 Requirements", "➕ Add Document Type"])

    # ─── TAB 1: Document Types with nested Requirements ───────────────────────
    with tab1:
        doc_types = run_async(get_document_types_api())
        if not doc_types:
            st.info("No document types configured yet. Add one in the '➕ Add Document Type' tab.")
        else:
            for dt in doc_types:
                with st.expander(f"📁 {dt['name']}  ·  `{dt['slug']}`", expanded=False):
                    if dt.get("description"):
                        st.markdown(f"<p style='color:#aaa;font-size:13px;'>{dt['description']}</p>", unsafe_allow_html=True)

                    reqs = run_async(get_requirements_by_type_api(dt["id"]))
                    if reqs:
                        for req in reqs:
                            mandatory = "🔴 Mandatory" if req.get("is_mandatory") else "🟡 Optional"
                            ocr_badge = "🤖 LLM Vision" if req.get("ocr_mode") == "llm_vision" else "📄 Tesseract"
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                st.markdown(f"""
                                <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px 16px;margin:6px 0;border:1px solid rgba(255,255,255,0.08);">
                                    <strong style="color:white;">{req['name']}</strong> &nbsp;
                                    <span style="color:#aaa;font-size:12px;">{mandatory} &nbsp; {ocr_badge}</span>
                                </div>""", unsafe_allow_html=True)
                            with col2:
                                if st.button("🗑️", key=f"del_req_{req['id']}"):
                                    if run_async(delete_requirement_api(req["id"])):
                                        st.success("Deleted")
                                        st.rerun()
                    else:
                        st.markdown("<p style='color:#666;font-size:13px;'>No requirements yet.</p>", unsafe_allow_html=True)

                    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:12px 0;'>", unsafe_allow_html=True)
                    col_del, _ = st.columns([1, 5])
                    with col_del:
                        if st.button(f"🗑️ Delete Type", key=f"del_dt_{dt['id']}"):
                            if run_async(delete_document_type_api(dt["id"])):
                                st.success(f"Deleted '{dt['name']}' and all its requirements.")
                                st.rerun()

    # ─── TAB 2: Add Requirement to an existing Document Type ──────────────────
    with tab2:
        doc_types = run_async(get_document_types_api())
        if not doc_types:
            st.warning("Add at least one document type first.")
        else:
            type_options = {dt["name"]: dt["id"] for dt in doc_types}
            with st.form("add_req_form"):
                selected_type_name = st.selectbox("Document Type *", list(type_options.keys()))
                name = st.text_input("Requirement Name *", placeholder="e.g. Aadhar Card")
                ocr_mode = st.selectbox("OCR Mode", ["tesseract", "llm_vision"],
                    help="tesseract = text/scanned docs | llm_vision = blueprints/images")
                is_mandatory = st.checkbox("Mandatory", value=True)
                add_btn = st.form_submit_button("➕ Add Requirement")

            if add_btn and name:
                payload = {
                    "document_type_id": type_options[selected_type_name],
                    "name": name,
                    "ocr_mode": ocr_mode,
                    "is_mandatory": is_mandatory
                }
                if run_async(add_requirement_api(payload)):
                    st.success(f"✅ '{name}' added under '{selected_type_name}'.")
                    st.rerun()
                else:
                    st.error("Failed. Ensure the FastAPI server is running.")

    # ─── TAB 3: Add new Document Type ─────────────────────────────────────────
    with tab3:
        with st.form("add_dt_form"):
            dt_name = st.text_input("Document Type Name *", placeholder="e.g. Land Records")
            dt_slug = st.text_input("Slug *", placeholder="e.g. land  (lowercase, no spaces)")
            dt_desc = st.text_area("Description", placeholder="What kind of documents belong to this type?")
            dt_btn = st.form_submit_button("➕ Add Document Type")

        if dt_btn and dt_name and dt_slug:
            payload = {"name": dt_name, "slug": dt_slug.lower().replace(" ", "_"), "description": dt_desc}
            if run_async(add_document_type_api(payload)):
                st.success(f"✅ Document type '{dt_name}' created. Now add requirements in the Requirements tab.")
                st.rerun()
            else:
                st.error("Failed. Ensure the FastAPI server is running.")



def main():
    if "stage" not in st.session_state:
        st.session_state["stage"] = None

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:20px 0;">
            <h2 style="font-size:22px;">🏛️ SaarthiAI</h2>
            <p style='color:#9090bb;font-size:12px;'>Government Scheme Portal</p>
        </div>
        <hr style='border-color:rgba(255,255,255,0.1);'>
        """, unsafe_allow_html=True)

        page = st.radio("Navigate", ["🏠 Citizen Portal", "⚙️ Admin Panel"], label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="position:absolute;bottom:20px;left:0;right:0;text-align:center;">
            <p style="color:#555;font-size:11px;">SaarthiAI v0.2 · AI-Gov Platform</p>
        </div>""", unsafe_allow_html=True)

    if "Citizen" in page:
        citizen_page()
    else:
        admin_page()

main()
