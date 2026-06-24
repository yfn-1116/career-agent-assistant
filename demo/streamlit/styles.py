"""DeepSeek-style minimal CSS for Internship Copilot."""

from __future__ import annotations
import streamlit as st

ACCENT = "#4D6BFE"
BORDER = "#e5e7eb"
TEXT = "#1a1a2e"
MUTED = "#6b7280"

CSS = f"""
<style>
/* ===== GLOBAL ===== */
.block-container {{
    max-width: 720px !important;
    padding: 7vh 1rem 1.5rem 1rem !important;
    margin: 0 auto !important;
}}
section[data-testid="stSidebar"] .block-container {{
    padding-top: 1rem !important;
}}
section[data-testid="stSidebar"] {{
    background: #fafbfc; border-right: 1px solid {BORDER};
}}

/* ===== EMPTY STATE ===== */
.empty-state {{
    text-align: center; padding: 3rem 0 1rem 0;
}}
.empty-state .logo {{
    width: 48px; height: 48px; background: {ACCENT}; border-radius: 14px;
    margin: 0 auto 1.5rem auto; display: flex; align-items: center;
    justify-content: center; font-size: 1.5rem; color: white;
}}
.empty-state h1 {{
    font-size: 1.6rem; font-weight: 700; color: {TEXT};
    margin-bottom: 0.3rem; letter-spacing: -0.01em;
}}
.empty-state .subtitle {{
    font-size: 0.9rem; color: {MUTED}; font-weight: 400;
    margin-bottom: 0; max-width: 400px; margin-left: auto; margin-right: auto;
}}

/* ===== CHAT INPUT (st.chat_input) ===== */
div[data-testid="stChatInput"] textarea {{
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    font-size: 0.95rem !important;
    min-height: 72px !important;
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}}
div[data-testid="stChatInput"] textarea:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px rgba(77,107,254,0.12) !important;
}}

/* send button */
div.stButton > button[kind="primary"] {{
    background: {ACCENT} !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.9rem !important; padding: 0.5rem 1.2rem !important;
}}
div.stButton > button[kind="primary"]:hover {{
    filter: brightness(1.08);
}}

/* ===== CHAT MESSAGES ===== */
.inline-metrics {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin: 0.5rem 0;
}}
.inline-metric {{
    background: white; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 0.5rem 0.6rem; text-align: center;
}}
.inline-metric .val {{ font-size: 1.1rem; font-weight: 700; color: {TEXT}; }}
.inline-metric .lbl {{ font-size: 0.68rem; color: {MUTED}; margin-top: 0.1rem; }}

.msg-card {{
    background: #f9fafb; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 0.9rem 1.1rem; margin: 0.5rem 0; font-size: 0.88rem;
    line-height: 1.6; white-space: pre-wrap;
}}
.msg-disclaimer {{ font-size: 0.75rem; color: {MUTED}; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid {BORDER}; }}

.advice-card {{
    background: white; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 0.9rem 1rem; margin: 0.5rem 0;
}}
.advice-card .jd-req {{ font-size: 0.8rem; color: {MUTED}; margin-bottom: 0.3rem; }}
.advice-card .rewrite {{ font-size: 0.88rem; color: {TEXT}; line-height: 1.55; margin: 0.3rem 0; padding: 0.4rem 0.7rem; background: #f9fafb; border-radius: 6px; }}
.advice-card .reason {{ font-size: 0.78rem; color: {MUTED}; margin: 0.3rem 0; }}
.advice-card .source {{ font-size: 0.73rem; color: {MUTED}; }}
.advice-card .status-tag {{ display: inline-block; font-size: 0.68rem; padding: 0.12rem 0.45rem; border-radius: 10px; margin-top: 0.3rem; }}
.advice-card .status-tag.can-write {{ background: #ecfdf3; color: #15803d; }}
.advice-card .status-tag.needs-confirm {{ background: #fff7ed; color: #c2410c; }}
.advice-card .status-tag.learn-only {{ background: #f3f4f6; color: #6b7280; }}

.risk-box {{
    background: #fef9f0; border: 1px solid #f0d89c; border-radius: 8px;
    padding: 0.6rem 0.9rem; margin: 0.5rem 0; font-size: 0.83rem; color: #8a6d3b;
}}

.ev-item {{ font-size: 0.8rem; padding: 0.3rem 0; border-bottom: 1px solid {BORDER}; line-height: 1.4; }}
.ev-item:last-child {{ border-bottom: none; }}
.ev-meta {{ font-size: 0.68rem; color: {MUTED}; margin-top: 0.08rem; }}
.ev-meta code {{ font-size: 0.66rem; background: #f9fafb; padding: 0.03rem 0.3rem; border-radius: 3px; }}

/* ===== SIDEBAR ===== */
.sidebar-profile {{ font-size: 0.78rem; color: {TEXT}; line-height: 1.5; padding: 0.2rem 0.2rem; }}
.sidebar-profile .label {{ font-size: 0.63rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.04em; }}
.sidebar-profile .val {{ font-weight: 500; }}
.sidebar-kb-stat {{ font-size: 0.78rem; color: {TEXT}; padding: 0.08rem 0.2rem; }}
.sidebar-kb-stat .num {{ font-weight: 700; color: {ACCENT}; }}
.sidebar-nav-section {{ font-size: 0.68rem; font-weight: 600; color: {MUTED}; padding: 0.4rem 0.2rem 0.12rem 0.2rem; }}
section[data-testid="stSidebar"] .stButton > button {{
    border-radius: 8px; border: 1px solid {BORDER}; background: white; font-size: 0.8rem;
}}
</style>
"""

def inject_custom_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
