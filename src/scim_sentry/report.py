from __future__ import annotations
import html, json
from collections import Counter
from pathlib import Path
from .models import Finding

def write_json(findings: list[Finding], path: Path) -> None:
    payload = {"summary": dict(Counter(f.severity for f in findings)), "count": len(findings), "findings": [f.to_dict() for f in findings]}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

def write_html(findings: list[Finding], path: Path) -> None:
    counts = Counter(f.severity for f in findings)
    cards = "".join(f'<div class="card"><b>{k}</b><span>{counts.get(k,0)}</span></div>' for k in ["critical","high","medium","low"])
    rows = []
    for f in findings:
        fix = html.escape(f.fix.action)
        if f.fix.method and f.fix.path:
            fix += f'<br><code>{html.escape(f.fix.method)} {html.escape(f.fix.path)}</code>'
        rows.append(f'<tr><td><b>{html.escape(f.severity)}</b></td><td><code>{html.escape(f.code)}</code></td><td>{html.escape(f.subject)}</td><td>{html.escape(f.message)}</td><td>{fix}</td></tr>')
    doc = f'''<!doctype html><meta charset="utf-8"><title>SCIM Sentry</title><style>body{{font:15px system-ui;background:#0b1020;color:#eef3ff;max-width:1200px;margin:40px auto;padding:0 20px}}h1{{font-size:42px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}.card{{background:#151d33;padding:18px;border-radius:14px;display:flex;justify-content:space-between}}.card span{{font-size:28px;font-weight:700}}table{{width:100%;border-collapse:collapse;margin-top:25px;background:#11182b}}th,td{{padding:11px;border-bottom:1px solid #28334e;text-align:left;vertical-align:top}}code{{color:#9ed7ff}}</style><h1>SCIM Sentry</h1><p>Directory drift and remediation report</p><div class="grid">{cards}</div><table><tr><th>Severity</th><th>Rule</th><th>Subject</th><th>Finding</th><th>Suggested fix</th></tr>{''.join(rows)}</table>'''
    path.write_text(doc, encoding="utf-8")
