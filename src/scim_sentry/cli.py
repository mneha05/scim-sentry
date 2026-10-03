from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from .adapters import entra, okta
from .demo import run as run_demo
from .directory import load_scim_directory
from .drift import check
from .report import write_html, write_json

def main() -> None:
    parser = argparse.ArgumentParser(prog="scim-sentry")
    sub = parser.add_subparsers(dest="cmd", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--provider", choices=["okta","entra"], default="okta")
    demo.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    demo.add_argument("--out", type=Path, default=Path("reports"))
    c = sub.add_parser("check")
    c.add_argument("--provider", choices=["okta","entra"], required=True)
    c.add_argument("--source", type=Path, required=True)
    c.add_argument("--directory", type=Path, required=True)
    c.add_argument("--out", type=Path, default=Path("reports/report.json"))
    c.add_argument("--html", type=Path)
    c.add_argument("--fail-on", choices=["critical","high","medium","low","never"], default="never")
    args = parser.parse_args()
    if args.cmd == "demo":
        findings = run_demo(args.provider, args.fixtures, args.out)
        print(f"provider={args.provider} findings={len(findings)} severity={dict(Counter(f.severity for f in findings))}")
        return
    source_payload = json.loads(args.source.read_text())
    directory_payload = json.loads(args.directory.read_text())
    source = okta.load(source_payload) if args.provider == "okta" else entra.load(source_payload)
    findings = check(source, load_scim_directory(directory_payload))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_json(findings, args.out)
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        write_html(findings, args.html)
    print(f"findings={len(findings)} severity={dict(Counter(f.severity for f in findings))}")
    rank = {"critical":4,"high":3,"medium":2,"low":1,"never":999}
    if args.fail_on != "never" and any(rank[f.severity] >= rank[args.fail_on] for f in findings):
        raise SystemExit(2)
