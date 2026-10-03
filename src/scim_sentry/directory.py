from __future__ import annotations
from .models import DirectorySnapshot
from .scim import group_from_scim, user_from_scim

def load_scim_directory(payload: dict) -> DirectorySnapshot:
    users = {u.id: u for u in (user_from_scim(x) for x in payload.get("Users", []))}
    groups = {g.id: g for g in (group_from_scim(x) for x in payload.get("Groups", []))}
    return DirectorySnapshot(provider="scim-directory", users=users, groups=groups)
