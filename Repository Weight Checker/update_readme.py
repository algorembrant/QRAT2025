#!/usr/bin/env python3
import re
from pathlib import Path

SUMMARY_PATH = Path("reports/summary.md")
README_PATH = Path("README.md")

START_TAG = "<!-- REPO_STATS_START -->"
END_TAG   = "<!-- REPO_STATS_END -->"

def main():
    if not SUMMARY_PATH.exists():
        print("summary.md not found.")
        return
    
    summary_text = SUMMARY_PATH.read_text()

    readme = README_PATH.read_text()

    pattern = re.compile(
        f"{START_TAG}.*?{END_TAG}", 
        re.DOTALL
    )

    replacement = f"{START_TAG}\n\n{summary_text}\n\n{END_TAG}"

    new_readme = re.sub(pattern, replacement, readme)

    README_PATH.write_text(new_readme, encoding="utf-8")
    print("README.md updated with summary.md")

if __name__ == "__main__":
    main()
