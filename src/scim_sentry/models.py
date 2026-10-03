from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"

@dataclass(frozen=True)
class User:
    id: str
    user_name: str
    email: str
    display_name: str
    active: bool = True
    external_id: str | None = None

    @property
    def identity_key(self) -> str:
        return (self.email or self.user_name).strip().lower()

@dataclass(frozen=True)
class Group:
    id: str
    display_name: str
    members: tuple[str, ...] = ()
    external_id: str | None = None

@dataclass
class DirectorySnapshot:
    provider: str
    users: dict[str, User] = field(default_factory=dict)
    groups: dict[str, Group] = field(default_factory=dict)

    def user_by_identity(self) -> dict[str, list[User]]:
        out: dict[str, list[User]] = {}
        for user in self.users.values():
            out.setdefault(user.identity_key, []).append(user)
        return out

@dataclass(frozen=True)
class SuggestedFix:
    action: str
    method: str | None = None
    path: str | None = None
    body: dict[str, Any] | None = None
    note: str | None = None

@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    subject: str
    message: str
    fix: SuggestedFix

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
