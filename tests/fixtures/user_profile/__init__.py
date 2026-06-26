"""User profile fixtures — 5 projects with realistic skill sets and statuses.

Usage::

    from tests.fixtures.user_profile import PROFILE_ITEMS, get_item
    agent_project = get_item("career-agent-assistant")
    all_items = PROFILE_ITEMS
"""

from __future__ import annotations

from career_agent.profile.schema import ProfileItem

from .career_agent_assistant import make_item as _agent_assistant
from .chem_auto_titration import make_item as _chem
from .dog_breed_cnn import make_item as _dog_breed
from .planned_mcp_support import make_item as _planned_mcp
from .smart_journey import make_item as _journey

PROFILE_ITEMS: list[ProfileItem] = [
    _agent_assistant(),
    _chem(),
    _journey(),
    _dog_breed(),
    _planned_mcp(),
]


def get_item(item_id: str) -> ProfileItem:
    """Return a ProfileItem fixture by item_id.  Returns None if not found."""
    for item in PROFILE_ITEMS:
        if item.item_id == item_id:
            return item
    return None
