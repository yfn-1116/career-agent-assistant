"""Realistic JD fixtures — 8 job types covering major internship categories.

Usage::

    from tests.fixtures.realistic_jobs import JOBS, get_jd
    agent_jd = JOBS["agent_intern"]
    jd = get_jd("cv_algorithm_intern")
"""

from __future__ import annotations

from career_agent.domain.schemas import ParsedJD

from .agent_intern import make_jd as _agent
from .ai_application_intern import make_jd as _ai_app
from .cv_algorithm_intern import make_jd as _cv
from .data_analyst_intern import make_jd as _data
from .frontend_intern import make_jd as _frontend
from .product_intern import make_jd as _product
from .python_backend_intern import make_jd as _backend
from .rag_intern import make_jd as _rag

JOBS: dict[str, ParsedJD] = {
    "agent_intern": _agent(),
    "rag_intern": _rag(),
    "ai_application_intern": _ai_app(),
    "python_backend_intern": _backend(),
    "cv_algorithm_intern": _cv(),
    "frontend_intern": _frontend(),
    "data_analyst_intern": _data(),
    "product_intern": _product(),
}


def get_jd(key: str) -> ParsedJD:
    """Return a ParsedJD fixture by key.  Raises KeyError for unknown keys."""
    if key not in JOBS:
        raise KeyError(f"Unknown JD fixture '{key}'. Available: {sorted(JOBS.keys())}")
    return JOBS[key]
