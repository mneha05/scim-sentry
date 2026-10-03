import json
from pathlib import Path
from scim_sentry.adapters import entra, okta
from scim_sentry.directory import load_scim_directory
from scim_sentry.drift import check

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
def load_json(name): return json.loads((FIXTURES / name).read_text())

def test_okta_detects_identity_and_membership_drift():
    findings = check(okta.load(load_json("okta_source.json")), load_scim_directory(load_json("directory.json")))
    codes = [f.code for f in findings]
    for expected in ["conflicting_source_identity","conflicting_directory_identity","active_state_mismatch","disabled_user_in_group","stale_membership","missing_membership","orphan_group_member"]:
        assert expected in codes
    disabled = next(f for f in findings if f.code == "disabled_user_in_group")
    assert disabled.fix.method == "PATCH"
    assert disabled.fix.path == "/scim/v2/Groups/dir-g1"
    assert disabled.fix.body["Operations"][0]["op"] == "Remove"

def test_entra_detects_disabled_user_and_missing_membership():
    findings = check(entra.load(load_json("entra_source.json")), load_scim_directory(load_json("directory.json")))
    codes = {f.code for f in findings}
    assert {"active_state_mismatch","disabled_user_in_group","missing_membership"} <= codes

def test_no_findings_when_directory_matches_source():
    source = entra.load(load_json("entra_source.json"))
    users, mapping = [], {}
    for i, user in enumerate(source.users.values(), 1):
        tid = f"target-{i}"; mapping[user.id] = tid
        users.append({"id":tid,"userName":user.user_name,"displayName":user.display_name,"active":user.active,"emails":[{"value":user.email,"type":"work","primary":True}]})
    groups = []
    for i, group in enumerate(source.groups.values(), 1):
        groups.append({
            "id":f"target-g{i}",
            "displayName":group.display_name,
            "members":[{"value":mapping[m]} for m in group.members if source.users[m].active]
        })
    assert check(source, load_scim_directory({"Users":users,"Groups":groups})) == []
