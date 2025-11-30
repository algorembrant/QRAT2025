#!/usr/bin/env python3
import os
import subprocess
import yaml
from pathlib import Path
import json
import sys
from datetime import datetime

def human_size(num_bytes: int, decimals: int = 2) -> str:
    if num_bytes == 0:
        return "0 Bytes"
    for unit in ['Bytes','KB','MB','GB','TB']:
        if num_bytes < 1024 or unit == 'TB':
            return f"{num_bytes:.{decimals}f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.{decimals}f} PB"

def repo_basic_stats(path: Path, skip_extensions=None):
    if skip_extensions is None:
        skip_extensions = set()
    total_size = 0
    total_files = 0
    total_lines = 0

    for root, dirs, files in os.walk(path):
        # optional: skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()
            if ext in skip_extensions:
                continue
            try:
                st = fp.stat()
                total_size += st.st_size
                total_files += 1
                # naive line count (binary files may still be counted)
                try:
                    with fp.open('rb') as fh:
                        total_lines += sum(1 for _ in fh)
                except Exception:
                    pass
            except Exception:
                pass
    return total_size, total_files, total_lines

def clone_or_update(repo_url: str, dest: Path, git_token=None):
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  Updating existing repo at {dest}")
        cmd = ["git", "-C", str(dest), "pull", "--ff-only"]
        env = os.environ.copy()
        if git_token and repo_url.startswith("https://"):
            # replace the host portion with token if needed (simple approach)
            cmd = ["git", "-C", str(dest), "pull", "--ff-only"]
            env["GIT_ASKPASS"] = "echo"
        subprocess.run(cmd, check=True, env=env)
    else:
        print(f"  Cloning {repo_url} -> {dest}")
        if git_token and repo_url.startswith("https://"):
            # insert token into URL for cloning: https://<token>@github.com/owner/repo.git
            url_with_token = repo_url.replace("https://", f"https://{git_token}@")
            subprocess.run(["git", "clone", url_with_token, str(dest)], check=True)
        else:
            subprocess.run(["git", "clone", repo_url, str(dest)], check=True)

def save_report(report: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"repo-stats-{ts}.json"
    out_file.write_text(json.dumps(report, indent=2))
    # Also write/overwrite latest.json
    latest = out_dir / "latest.json"
    latest.write_text(json.dumps(report, indent=2))
    print(f"Report written: {out_file}")
    return out_file

def main():
    cfg_path = Path("repos.yml")
    if not cfg_path.exists():
        print("repos.yml not found. Create it first.", file=sys.stderr)
        sys.exit(2)

    cfg = yaml.safe_load(cfg_path.read_text())
    git_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")  # optional token for private repos
    overall = {"generated_at": datetime.utcnow().isoformat()+"Z", "repos": []}

    for r in cfg.get("repos", []):
        name = r.get("name")
        url = r.get("url")
        local = Path(r.get("local_path", f"./repos/{name}"))
        skip_exts = set((r.get("skip_extensions") or []))
        print(f"Processing repo: {name}")
        try:
            clone_or_update(url, local, git_token=git_token)
        except subprocess.CalledProcessError as e:
            print(f"  Git operation failed for {name}: {e}", file=sys.stderr)
            overall["repos"].append({"name": name, "error": str(e)})
            continue

        size, n_files, n_lines = repo_basic_stats(local, skip_extensions=skip_exts)
        repo_info = {
            "name": name,
            "url": url,
            "local_path": str(local),
            "total_size_bytes": size,
            "total_size_human": human_size(size),
            "file_count": n_files,
            "line_count": n_lines
        }
        print(f"  files: {n_files}")
        print(f"  total size: {size} bytes ({human_size(size)})")
        print(f"  total lines (naive): {n_lines}")
        overall["repos"].append(repo_info)

    out = save_report(overall, Path("reports"))
    print("Done. Latest report:", out)

if __name__ == "__main__":
    main()
