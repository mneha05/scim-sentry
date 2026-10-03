from __future__ import annotations
import json
from pathlib import Path
from .adapters import entra, okta
from .directory import load_scim_directory
from .drift import check
from .report import write_html, write_json

def run(provider: str, fixtures: Path, out: Path):
    source_payload = json.loads((fixtures / f"{provider}_source.json").read_text())
    target_payload = json.loads((fixtures / "directory.json").read_text())
    source = okta.load(source_payload) if provider == "okta" else entra.load(source_payload)
    findings = check(source, load_scim_directory(target_payload))
    out.mkdir(parents=True, exist_ok=True)
    write_json(findings, out / f"{provider}-report.json")
    write_html(findings, out / f"{provider}-report.html")
    return findings
