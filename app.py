from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.auth import create_otp_state, verify_otp
from src.customer_db import answer_customer_query, find_customer_by_email
from src.document_rag import format_sources, load_or_build_vector_store
from src.llm import generate_document_answer
from src.router import classify_query
from src.settings import get_factsheet_path


st.set_page_config(page_title="HDFC MF AI Chatbot", page_icon="AI", layout="wide")

SAMPLE_EMAILS = [
    "aryan.shukla@example.com",
    "richa.tiwari@example.com",
    "omkar.dhavalikar@example.com",
]


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #0b0f16;
            --panel: #151a23;
            --panel-soft: #1f2632;
            --line: rgba(255, 255, 255, 0.12);
            --text-soft: #aeb7c6;
            --accent: #2f80ed;
            --success-bg: #173d2d;
            --success-border: #2e9d65;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 4.5rem;
            padding-bottom: 6rem;
        }

        h1 {
            letter-spacing: 0;
            font-size: 2.45rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0.35rem !important;
        }

        [data-testid="stSidebar"] {
            background: #242731;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.72rem;
        }

        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            font-size: 1rem !important;
            margin-top: 0.4rem !important;
            margin-bottom: 0.25rem !important;
        }

        [data-testid="stSidebar"] label {
            font-size: 0.82rem !important;
            color: #f4f6fb !important;
        }

        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            min-height: 2.45rem;
            border-radius: 0.5rem;
            border-color: rgba(255, 255, 255, 0.22);
            font-weight: 600;
        }

        [data-testid="stSidebar"] input {
            border-radius: 0.5rem;
        }

        div[data-testid="stAlert"] {
            border-radius: 0.55rem;
        }

        .side-card {
            border: 1px solid var(--line);
            background: var(--panel-soft);
            border-radius: 0.6rem;
            padding: 0.78rem 0.92rem;
            margin: 0.35rem 0 0.55rem;
        }

        .side-card.success {
            background: var(--success-bg);
            border-color: rgba(46, 157, 101, 0.55);
        }

        .side-card .label {
            color: var(--text-soft);
            font-size: 0.74rem;
            line-height: 1.2;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
        }

        .side-card .value {
            color: #ffffff;
            font-size: 0.92rem;
            line-height: 1.38;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .otp-box {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.45rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: #10141d;
            border-radius: 0.6rem;
            padding: 0.72rem 0.84rem;
            margin-bottom: 0.5rem;
        }

        .otp-box .otp {
            color: #38d9a9;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.08rem;
            font-family: Consolas, Monaco, monospace;
        }

        .sample-email {
            display: block;
            padding: 0.45rem 0.62rem;
            margin: 0.35rem 0;
            color: #d8e6ff !important;
            background: #111722;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.48rem;
            overflow-wrap: anywhere;
            font-size: 0.82rem;
        }

        .stChatMessage {
            border-radius: 0.65rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session() -> None:
    defaults = {
        "messages": [],
        "pending_customer_query": None,
        "otp_state": None,
        "authenticated_customer_id": None,
        "simulated_outbox": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.cache_resource(show_spinner=False)
def get_vector_store(pdf_path: str, force_rebuild: bool = False):
    return load_or_build_vector_store(Path(pdf_path), force_rebuild=force_rebuild)


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def reset_authentication() -> None:
    st.session_state.authenticated_customer_id = None
    st.session_state.otp_state = None
    st.session_state.pending_customer_query = None


def handle_document_query(query: str, pdf_path: Path) -> str:
    store = get_vector_store(str(pdf_path))
    results = store.search(query, top_k=5)
    if not results:
        return "I could not find relevant content in the factsheet for that question."

    context = format_sources(results)
    answer = generate_document_answer(query, context)
    source_pages = sorted({chunk.page for chunk, _score in results})
    return f"{answer}\n\nSources: factsheet page(s) {', '.join(map(str, source_pages))}"


def handle_customer_query(query: str) -> str:
    authenticated_id = st.session_state.get("authenticated_customer_id")
    if authenticated_id:
        return answer_customer_query(query, authenticated_id)

    st.session_state.pending_customer_query = query
    return "This looks like a customer-specific query. Please enter your registered email ID in the 2FA panel to continue."


def handle_security_query() -> str:
    return (
        "I cannot reveal database contents, bypass authentication, or show another customer's information. "
        "Please ask factsheet questions or authenticated questions about the current customer only."
    )


def render_side_card(label: str, value: str, style: str = "") -> None:
    st.sidebar.markdown(
        f"""
        <div class="side-card {style}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_outbox_item(item: dict | str) -> None:
    if isinstance(item, dict):
        email = item.get("email", "unknown@example.com")
        otp = item.get("otp", "------")
    else:
        email = item
        otp = "------"
        if "| OTP:" in item:
            email_part, otp_part = item.split("| OTP:", 1)
            email = email_part.replace("To:", "").strip()
            otp = otp_part.strip()

    st.sidebar.markdown(
        f"""
        <div class="otp-box">
            <div>
                <div class="label">To</div>
                <div class="value">{email}</div>
            </div>
            <div>
                <div class="label">OTP</div>
                <div class="otp">{otp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(pdf_path: Path | None) -> None:
    st.sidebar.header("Control Panel")

    if pdf_path:
        render_side_card("Factsheet", f"Loaded: {pdf_path.name}", "success")
        if st.sidebar.button("Rebuild factsheet vector store"):
            get_vector_store.clear()
            get_vector_store(str(pdf_path), force_rebuild=True)
            st.sidebar.success("Vector store rebuilt.")
    else:
        st.sidebar.error("Factsheet PDF not found.")
        st.sidebar.caption("Set FACTSHEET_PATH or place the PDF inside the data folder.")

    st.sidebar.divider()
    st.sidebar.subheader("2FA Panel")
    if st.session_state.authenticated_customer_id:
        render_side_card("Status", f"Authenticated: {st.session_state.authenticated_customer_id}", "success")
        if st.sidebar.button("Reset authentication"):
            reset_authentication()
            st.rerun()

    email = st.sidebar.text_input("Registered email")
    if st.sidebar.button("Send OTP"):
        customer = find_customer_by_email(email)
        if not customer:
            st.sidebar.error("Email ID not found in customer records.")
        else:
            otp_state = create_otp_state(customer["email"], customer["customer_id"])
            st.session_state.otp_state = otp_state
            st.session_state.authenticated_customer_id = None
            st.session_state.simulated_outbox.append({"email": customer["email"], "otp": otp_state["otp"]})
            st.sidebar.success("OTP generated in the simulated email outbox.")

    submitted_otp = st.sidebar.text_input("OTP", type="password")
    if st.sidebar.button("Verify OTP"):
        ok, message = verify_otp(st.session_state.get("otp_state"), submitted_otp)
        if ok:
            st.session_state.authenticated_customer_id = st.session_state.otp_state["customer_id"]
            st.sidebar.success(message)
            pending_query = st.session_state.get("pending_customer_query")
            if pending_query:
                answer = answer_customer_query(pending_query, st.session_state.authenticated_customer_id)
                add_message("assistant", answer)
                st.session_state.pending_customer_query = None
        else:
            st.sidebar.error(message)

    if st.session_state.simulated_outbox:
        st.sidebar.divider()
        st.sidebar.subheader("Simulated Email Outbox")
        for item in st.session_state.simulated_outbox[-3:]:
            render_outbox_item(item)

    st.sidebar.divider()
    st.sidebar.subheader("Sample Login Emails")
    for sample_email in SAMPLE_EMAILS:
        st.sidebar.markdown(f'<span class="sample-email">{sample_email}</span>', unsafe_allow_html=True)


def main() -> None:
    apply_theme()
    init_session()
    pdf_path = get_factsheet_path()

    st.title("HDFC MF Generative AI Chatbot")
    st.caption("Factsheet RAG + customer data access + 2FA flow")

    render_sidebar(pdf_path)

    if not pdf_path:
        st.warning("Factsheet PDF is missing. Customer authentication still works, but document Q&A needs the PDF.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    query = st.chat_input("Ask about the factsheet or your customer portfolio")
    if not query:
        return

    add_message("user", query)
    with st.chat_message("user"):
        st.markdown(query)

    route = classify_query(query)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if route == "customer":
                answer = handle_customer_query(query)
            elif route == "security":
                answer = handle_security_query()
            elif pdf_path:
                answer = handle_document_query(query, pdf_path)
            else:
                answer = "Factsheet PDF is not available, so I cannot answer document questions yet."
        st.markdown(answer)
    add_message("assistant", answer)


if __name__ == "__main__":
    main()
