"""Minimal Chat-first CSS for Internship Copilot Streamlit UI."""

from __future__ import annotations

import streamlit as st

ACCENT = "#4F5FD7"
BORDER = "#e5e7eb"
BG = "#f9fafb"
TEXT = "#111827"
MUTED = "#6b7280"

CSS = f"""
<style>
.block-container {{ padding-top: 1.5rem; max-width: 800px; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 0.8rem; }}
section[data-testid="stSidebar"] {{ background: #fafbfc; border-right: 1px solid {BORDER}; }}

/* chat input */
div[data-testid="stChatInput"] textarea {{
    border: 1px solid {BORDER} !important; border-radius: 12px !important;
    padding: 0.8rem 1rem !important; font-size: 0.92rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important; min-height: 52px !important;
}}
div[data-testid="stChatInput"] textarea:focus {{
    border-color: {ACCENT} !important; box-shadow: 0 0 0 3px rgba(79,95,215,0.1) !important;
}}

/* empty state */
.empty-state {{ text-align: center; padding: 3rem 2rem 1rem 2rem; }}
.empty-state h1 {{ font-size: 1.8rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.02em; margin-bottom: 0.3rem; }}
.empty-state .subtitle {{ font-size: 0.92rem; color: {MUTED}; margin-bottom: 1.5rem; }}

/* metrics */
.inline-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin: 0.6rem 0; }}
.inline-metric {{ background: white; border: 1px solid {BORDER}; border-radius: 8px; padding: 0.6rem 0.7rem; text-align: center; }}
.inline-metric .val {{ font-size: 1.15rem; font-weight: 700; color: {TEXT}; }}
.inline-metric .lbl {{ font-size: 0.7rem; color: {MUTED}; margin-top: 0.15rem; }}

/* message card */
.msg-card {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 0.9rem 1.1rem; margin: 0.5rem 0; font-size: 0.88rem; line-height: 1.6; white-space: pre-wrap; }}
.msg-disclaimer {{ font-size: 0.75rem; color: {MUTED}; margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px solid {BORDER}; }}

/* resume advice card */
.advice-card {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 1rem 1.2rem; margin: 0.7rem 0; }}
.advice-card .jd-req {{ font-size: 0.82rem; color: {MUTED}; margin-bottom: 0.4rem; }}
.advice-card .rewrite {{ font-size: 0.9rem; color: {TEXT}; line-height: 1.6; margin: 0.4rem 0; padding: 0.5rem 0.8rem; background: {BG}; border-radius: 6px; }}
.advice-card .reason {{ font-size: 0.8rem; color: {MUTED}; margin: 0.3rem 0; }}
.advice-card .source {{ font-size: 0.75rem; color: {MUTED}; }}
.advice-card .status-tag {{ display: inline-block; font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 10px; margin-top: 0.3rem; }}
.advice-card .status-tag.can-write {{ background: #ecfdf3; color: #15803d; }}
.advice-card .status-tag.needs-confirm {{ background: #fff7ed; color: #c2410c; }}
.advice-card .status-tag.learn-only {{ background: #f3f4f6; color: #6b7280; }}

/* risk box */
.risk-box {{ background: #fef9f0; border: 1px solid #f0d89c; border-radius: 8px; padding: 0.7rem 1rem; margin: 0.6rem 0; font-size: 0.85rem; color: #8a6d3b; }}

/* evidence */
.ev-item {{ font-size: 0.82rem; padding: 0.35rem 0; border-bottom: 1px solid {BORDER}; line-height: 1.45; }}
.ev-item:last-child {{ border-bottom: none; }}
.ev-meta {{ font-size: 0.7rem; color: {MUTED}; margin-top: 0.1rem; }}
.ev-meta code {{ font-size: 0.68rem; background: {BG}; padding: 0.03rem 0.3rem; border-radius: 3px; }}

/* sidebar profile */
.sidebar-profile {{ font-size: 0.8rem; color: {TEXT}; line-height: 1.5; padding: 0.3rem 0.2rem; }}
.sidebar-profile .label {{ font-size: 0.65rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.04em; }}
.sidebar-profile .val {{ font-weight: 500; }}

/* sidebar kb */
.sidebar-kb-stat {{ font-size: 0.8rem; color: {TEXT}; padding: 0.1rem 0.2rem; }}
.sidebar-kb-stat .num {{ font-weight: 700; color: {ACCENT}; }}
.sidebar-nav-section {{ font-size: 0.7rem; font-weight: 600; color: {MUTED}; padding: 0.5rem 0.2rem 0.15rem 0.2rem; }}

/* buttons */
div.stButton > button[kind="primary"] {{ background: {ACCENT} !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; }}
div.stButton > button[kind="primary"]:disabled {{ background: #d1d5db !important; color: #9ca3af !important; }}
section[data-testid="stSidebar"] .stButton > button {{ border-radius: 8px; border: 1px solid {BORDER}; background: white; font-size: 0.82rem; }}

/* skeleton */
.skeleton-block {{ background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; height: 40px; margin: 0.4rem 0; }}
@keyframes shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}
</style>
"""

def inject_custom_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
