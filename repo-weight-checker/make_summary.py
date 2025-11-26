#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

def generate_summary(report_path: Path, output_path: Path):
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    data = json.loads(report_path.read_text())

    generated_at = data.get("generated_at", "unknown")
    repos = data.get("repos", [])

    lines = []
    lines.append("# 📊 Repository Size Summary")
    lines.append("")
    lines.append(f"**Last Updated:** `{generated_at}`")
    lines.append("")
    lines.append("| Repository | Size | Files | Lines | Status |")
    lines.append("|-----------|-------|--------|--------|---------|")

    for r in repos:
        name = r.get("name", "unknown")
        size = r.get("total_size_human", "N/A")
        files = r.get("file_count", "N/A")
        line_count = r.get("line_count", "N/A")

        if "error" in r:
            status = f"❌ Error"
            lines.append(f"| {name} | - | - | - | {status} |")
        else:
            status = "✅ OK"
            lines.append(f"| {name} | {size} | {files} | {line_count:,} | {status} |")

    # Long form details
    lines.append("")
    lines.append("---")
    lines.append("## 📁 Detailed Report")
    lines.append("")

    for r in repos:
        name = r.get("name", "unknown")
        lines.append(f"### {name}")
        if "error" in r:
            lines.append(f"❌ Error collecting stats: `{r['error']}`")
            lines.append("")
            continue

        lines.append(f"- **URL:** {r.get('url')}")
        lines.append(f"- **Local Path:** `{r.get('local_path')}`")
        lines.append(f"- **Total Size:** {r.get('total_size_human')} ({r.get('total_size_bytes')} bytes)")
        lines.append(f"- **Files:** {r.get('file_count')}")
        lines.append(f"- **Lines:** {r.get('line_count'):,}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("Generated summary:", output_path)

def main():
    report_path = Path("reports/latest.json")
    output_path = Path("reports/summary.md")
    generate_summary(report_path, output_path)

if __name__ == "__main__":
    main()
