from __future__ import annotations
from .models import DirectorySnapshot, Finding, SuggestedFix
from .scim import patch_add_member, patch_remove_member, patch_replace_active

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def _group_by_name(snapshot: DirectorySnapshot):
    return {g.display_name.strip().lower(): g for g in snapshot.groups.values()}

def check(source: DirectorySnapshot, target: DirectorySnapshot) -> list[Finding]:
    findings: list[Finding] = []
    source_ids = source.user_by_identity()
    target_ids = target.user_by_identity()

    for identity, users in source_ids.items():
        if len(users) > 1:
            findings.append(Finding(
                "conflicting_source_identity", "high", identity,
                f"Multiple {source.provider} users resolve to {identity}: {', '.join(u.id for u in users)}",
                SuggestedFix("review_identity_conflict", note="Choose the authoritative identity before provisioning.")))

    for identity, users in target_ids.items():
        if len(users) > 1:
            findings.append(Finding(
                "conflicting_directory_identity", "high", identity,
                f"Multiple SCIM directory users resolve to {identity}: {', '.join(u.id for u in users)}",
                SuggestedFix("deduplicate_directory_identity", note="Merge or deprovision the duplicate directory account.")))

    for identity, users in source_ids.items():
        if len(users) != 1:
            continue
        src = users[0]
        targets = target_ids.get(identity, [])
        if not targets:
            findings.append(Finding(
                "missing_directory_user", "high", identity,
                f"Source identity {identity} is not present in the SCIM directory.",
                SuggestedFix("provision_user", method="POST", path="/scim/v2/Users", note="Provision with the SCIM core User schema.")))
            continue
        if len(targets) != 1:
            continue
        dst = targets[0]
        if src.active != dst.active:
            patch = patch_replace_active(dst.id, src.active)
            findings.append(Finding(
                "active_state_mismatch", "critical" if not src.active else "high", identity,
                f"Source active={src.active} but directory active={dst.active}.",
                SuggestedFix("align_active_state", patch["method"], patch["path"], patch["body"])))

    source_groups = _group_by_name(source)
    target_groups = _group_by_name(target)

    for name, src_group in source_groups.items():
        dst_group = target_groups.get(name)
        if not dst_group:
            findings.append(Finding(
                "missing_directory_group", "medium", src_group.display_name,
                "Source group is not present in the SCIM directory.",
                SuggestedFix("provision_group", method="POST", path="/scim/v2/Groups", note="Create the group, then add in-scope members.")))
            continue

        desired = {source.users[m].identity_key for m in src_group.members if m in source.users and source.users[m].active}
        actual = {target.users[m].identity_key for m in dst_group.members if m in target.users}

        for member_id in dst_group.members:
            user = target.users.get(member_id)
            if user is None:
                patch = patch_remove_member(dst_group.id, member_id)
                findings.append(Finding(
                    "orphan_group_member", "high", f"{dst_group.display_name}:{member_id}",
                    "Group references a directory user that does not exist.",
                    SuggestedFix("remove_orphan_member", patch["method"], patch["path"], patch["body"])))
                continue

            source_matches = source_ids.get(user.identity_key, [])
            source_disabled = len(source_matches) == 1 and not source_matches[0].active
            if not user.active or source_disabled:
                patch = patch_remove_member(dst_group.id, user.id)
                findings.append(Finding(
                    "disabled_user_in_group", "critical", f"{dst_group.display_name}:{user.identity_key}",
                    "Disabled source/directory user still retains group membership.",
                    SuggestedFix("remove_disabled_membership", patch["method"], patch["path"], patch["body"])))

        for identity in sorted(actual - desired):
            matches = target_ids.get(identity, [])
            if len(matches) == 1 and matches[0].active:
                patch = patch_remove_member(dst_group.id, matches[0].id)
                findings.append(Finding(
                    "stale_membership", "high", f"{dst_group.display_name}:{identity}",
                    "Directory membership is not present in the source-of-truth group.",
                    SuggestedFix("remove_stale_membership", patch["method"], patch["path"], patch["body"])))

        for identity in sorted(desired - actual):
            matches = target_ids.get(identity, [])
            if len(matches) == 1:
                patch = patch_add_member(dst_group.id, matches[0].id)
                findings.append(Finding(
                    "missing_membership", "medium", f"{dst_group.display_name}:{identity}",
                    "Source-of-truth membership is missing from the SCIM directory.",
                    SuggestedFix("add_missing_membership", patch["method"], patch["path"], patch["body"])))

    return sorted(findings, key=lambda f: (SEVERITY_RANK.get(f.severity, 9), f.code, f.subject))
