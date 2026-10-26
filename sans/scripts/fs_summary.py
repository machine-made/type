"""Summarize Fontspector JSON reports.

Usage:
    python sans/scripts/fs_summary.py REPORT.json [REPORT.json ...] [--md OUT.md]

Prints one line per check that is not PASS, SKIP or INFO, with the files
and the messages. Exit status is 1 if a check has FAIL, ERROR or FATAL.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BAD = {"FAIL", "ERROR", "FATAL"}
SHOW = BAD | {"WARN"}


def checks(results):
    for _section_group, sections in results.items():
        for _section, items in sections.items():
            yield from items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="+", type=Path)
    ap.add_argument("--md", type=Path)
    args = ap.parse_args(argv)
    rows = defaultdict(lambda: {"files": set(), "messages": set()})
    totals = {}
    bad = False
    for rep in args.reports:
        data = json.loads(rep.read_text(encoding="utf-8"))
        totals[rep.name] = data.get("summary", {})
        for c in checks(data["results"]):
            for sub in c.get("subresults", []):
                sev = sub.get("severity")
                if sev not in SHOW:
                    continue
                bad |= sev in BAD
                key = (sev, c["check_id"], sub.get("code", ""))
                rows[key]["files"].add(Path(c.get("filename", "")).name)
                msg = " ".join(str(sub.get("message", "")).split())
                rows[key]["messages"].add(msg[:300])
    out = ["| Report | Summary |", "| --- | --- |"]
    for name, s in totals.items():
        out.append(f"| {name} | " + ", ".join(f"{k} {v}" for k, v in sorted(s.items())) + " |")
    out += ["", "| Status | Check | Code | Files | Message (first) |", "| --- | --- | --- | --- | --- |"]
    for (sev, cid, code), v in sorted(rows.items()):
        files = ", ".join(sorted(v["files"]))
        msg = sorted(v["messages"])[0].replace("|", "/")
        out.append(f"| {sev} | {cid} | {code} | {files} | {msg} |")
    text = "\n".join(out) + "\n"
    print(text)
    if args.md:
        args.md.write_text(text, encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
