# SCIM Sentry

**Directory drift checker for SCIM 2.0, Okta-style, and Microsoft Entra-style identity data.**

SCIM Sentry compares an identity provider's users/groups with a target SCIM directory and flags lifecycle or membership drift with concrete remediation guidance.

## Detects

- conflicting identities resolving to the same email/username;
- source users missing from the directory;
- source-vs-directory `active` state mismatches;
- **disabled users still present in groups**;
- stale memberships existing only in the target;
- missing memberships existing only in the source of truth;
- orphan group members referencing deleted identities;
- source groups missing from the directory.

Each actionable finding includes a suggested SCIM remediation. Example:

```json
{
  "action": "remove_disabled_membership",
  "method": "PATCH",
  "path": "/scim/v2/Groups/dir-g1",
  "body": {
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{"op": "Remove", "path": "members[value eq \"dir-u2\"]"}]
  }
}
```

## Provider adapters

- **Okta-style:** `profile.login`, `profile.email`, lifecycle `status`, groups and member IDs.
- **Microsoft Entra-style:** `userPrincipalName`, `mail`, `accountEnabled`, groups and member IDs.
- **Target directory:** SCIM 2.0 User/Group shapes.

The fixtures are mock exports. This project does **not** claim access to a real enterprise Okta or Entra tenant.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
scim-sentry demo --provider okta --out reports
scim-sentry demo --provider entra --out reports
```

For your own exports:

```bash
scim-sentry check \
  --provider entra \
  --source my-entra-export.json \
  --directory my-scim-directory.json \
  --out reports/drift.json \
  --html reports/drift.html \
  --fail-on high
```

`--fail-on high` exits non-zero when high/critical drift exists, so it can be used as a CI/compliance gate.

## Architecture

```text
Okta export -----\
                  +--> provider adapter --> normalized users/groups --+
Entra export ----/                                                    |
                                                                     +--> drift engine --> JSON / HTML
SCIM directory ------------------> SCIM parser -----------------------+                  +--> PATCH suggestions
```

## Directory concepts demonstrated

- SCIM User and Group resources;
- account lifecycle and deprovisioning through `active`;
- provider-independent identity matching;
- groups and memberships;
- stale/missing/orphan membership reconciliation;
- SCIM PatchOp remediation for `Users` and `Groups`.

## Honest boundary

This is a drift/reconciliation layer over **mock Okta/Entra exports** and SCIM-shaped directory data. It demonstrates hands-on SCIM, user/group lifecycle, memberships, provisioning/deprovisioning logic, and remediation payloads. It does not claim production tenant administration or ownership of enterprise identity infrastructure.

## License

MIT
