from __future__ import annotations
from ..models import DirectorySnapshot, Group, User

def load(payload: dict) -> DirectorySnapshot:
    users = {}
    for row in payload.get("users", []):
        upn = str(row.get("userPrincipalName", ""))
        user = User(id=str(row["id"]), external_id=str(row["id"]), user_name=upn,
                    email=str(row.get("mail") or upn), display_name=str(row.get("displayName", upn)),
                    active=bool(row.get("accountEnabled", True)))
        users[user.id] = user
    groups = {}
    for row in payload.get("groups", []):
        group = Group(id=str(row["id"]), external_id=str(row["id"]),
                      display_name=str(row.get("displayName", "")),
                      members=tuple(str(x) for x in row.get("members", [])))
        groups[group.id] = group
    return DirectorySnapshot(provider="entra", users=users, groups=groups)
