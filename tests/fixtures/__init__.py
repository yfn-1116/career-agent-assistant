"""Test fixtures — realistic job descriptions and user profile items.

All fixtures are Python modules that construct project dataclasses.
No JSON, no Markdown parsing, no network access.
"""

from tests.fixtures.realistic_jobs import JOBS, get_jd
from tests.fixtures.user_profile import PROFILE_ITEMS, get_item

__all__ = ["JOBS", "get_jd", "PROFILE_ITEMS", "get_item"]
