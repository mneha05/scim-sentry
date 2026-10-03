from scim_sentry.scim import patch_add_member, patch_remove_member, patch_replace_active
from scim_sentry.models import SCIM_PATCH_SCHEMA

def test_patch_payloads_use_scim_patch_schema():
    for patch in [patch_replace_active("u1", False), patch_remove_member("g1", "u1"), patch_add_member("g1", "u1")]:
        assert patch["method"] == "PATCH"
        assert patch["body"]["schemas"] == [SCIM_PATCH_SCHEMA]
        assert patch["body"]["Operations"]
