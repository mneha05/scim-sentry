from __future__ import annotations
from .models import SCIM_PATCH_SCHEMA, Group, User

def user_from_scim(resource: dict) -> User:
    emails = resource.get("emails") or []
    primary = next((e for e in emails if e.get("primary")), None) or (emails[0] if emails else {})
    return User(
        id=str(resource["id"]), external_id=resource.get("externalId"),
        user_name=str(resource.get("userName", "")),
        email=str(primary.get("value", resource.get("userName", ""))),
        display_name=str(resource.get("displayName", resource.get("userName", ""))),
        active=bool(resource.get("active", True)),
    )

def group_from_scim(resource: dict) -> Group:
    return Group(
        id=str(resource["id"]), external_id=resource.get("externalId"),
        display_name=str(resource.get("displayName", "")),
        members=tuple(str(m["value"]) for m in resource.get("members", []) if m.get("value")),
    )

def patch_replace_active(user_id: str, active: bool) -> dict:
    return {"method":"PATCH","path":f"/scim/v2/Users/{user_id}","body":{
        "schemas":[SCIM_PATCH_SCHEMA],"Operations":[{"op":"Replace","path":"active","value":active}]}}

def patch_remove_member(group_id: str, user_id: str) -> dict:
    return {"method":"PATCH","path":f"/scim/v2/Groups/{group_id}","body":{
        "schemas":[SCIM_PATCH_SCHEMA],"Operations":[{"op":"Remove","path":f'members[value eq "{user_id}"]'}]}}

def patch_add_member(group_id: str, user_id: str) -> dict:
    return {"method":"PATCH","path":f"/scim/v2/Groups/{group_id}","body":{
        "schemas":[SCIM_PATCH_SCHEMA],"Operations":[{"op":"Add","path":"members","value":[{"value":user_id}]}]}}
