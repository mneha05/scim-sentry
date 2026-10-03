from __future__ import annotations
from ..models import DirectorySnapshot, Group, User

def load(payload: dict) -> DirectorySnapshot:
    users = {}
    for row in payload.get("users", []):
        profile = row.get("profile", {})
        user = User(
            id=str(row["id"]), external_id=str(row["id"]),
            user_name=str(profile.get("login", "")),
            email=str(profile.get("email", profile.get("login", ""))),
            display_name=str(profile.get("displayName") or f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()),
            active=str(row.get("status", "ACTIVE")).upper() not in {"DEPROVISIONED","SUSPENDED","LOCKED_OUT"},
        )
        users[user.id] = user
    groups = {}
    for row in payload.get("groups", []):
        group = Group(id=str(row["id"]), external_id=str(row["id"]),
                      display_name=str(row.get("profile", {}).get("name", row.get("name", ""))),
                      members=tuple(str(x) for x in row.get("members", [])))
        groups[group.id] = group
    return DirectorySnapshot(provider="okta", users=users, groups=groups)
