#!/usr/bin/env python3
"""Read-only reconciliation of local projects against GitHub repos.

Usage: project_github_audit.py [--map PATH] [--fetch] [--json]
Exit codes: 0 all clean, 1 findings needing attention, 2 scan/environment failure.
Never commits, pushes, renames, or changes visibility.
"""
import argparse
import json
import os
import subprocess
import sys

COLS = ["pid", "kind", "local_path", "display_name", "repo", "visibility", "note"]


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git(cwd, *args):
    return sh(["git", "-C", cwd, *args])


def read_map(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            parts += [""] * (len(COLS) - len(parts))
            rows.append(dict(zip(COLS, parts)))
    return rows


def gh_repo(name):
    out = sh(["gh", "repo", "view", f"wanghoufan/{name}", "--json",
              "visibility,isArchived,defaultBranchRef,isEmpty"])
    if out.returncode != 0:
        return None
    data = json.loads(out.stdout)
    data["default"] = (data.get("defaultBranchRef") or {}).get("name", "")
    return data


def audit_row(row, root, fetch):
    """Return (status_flags, facts dict)."""
    flags, facts = [], {}
    path = os.path.join(root, row["local_path"]) if row["local_path"] not in ("", "-") else ""
    kind = row["kind"]

    if kind == "orphan":
        info = gh_repo(row["repo"]) if row["repo"] else None
        if info is None:
            flags.append("REMOTE_NOT_FOUND")
        else:
            flags.append("GITHUB_ORPHAN")
        facts["repo"] = row["repo"]
        facts["visibility"] = info["visibility"] if info else "?"
        facts["no_backup_check"] = True
        return flags, facts

    if not os.path.isdir(path):
        return ["NEEDS_MANUAL_REVIEW"], {"error": "local dir missing"}
    if git(path, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return ["NOT_GIT"], {"local": path}

    facts["local"] = path
    facts["branch"] = git(path, "branch", "--show-current").stdout.strip()
    url = git(path, "remote", "get-url", "origin")
    if url.returncode != 0:
        flags.append("NO_ORIGIN")
        return flags, facts
    origin = url.stdout.strip()
    facts["origin"] = origin

    owner_slug = origin.rstrip("/").removesuffix(".git").split("github.com/")[-1]
    facts["remote_slug"] = owner_slug
    if not owner_slug.startswith("wanghoufan/"):
        flags.append("REMOTE_NOT_FOUND")
        return flags, facts
    repo_name = owner_slug.split("/", 1)[1]
    if row["repo"] and repo_name != row["repo"]:
        flags.append("MAPPING_MISMATCH")
    facts["repo"] = repo_name

    info = gh_repo(repo_name)
    if info is None:
        flags.append("REMOTE_NOT_FOUND")
        return flags, facts
    facts["visibility"] = info["visibility"]
    if row["visibility"] and info["visibility"] != row["visibility"]:
        flags.append("VISIBILITY_DRIFT")

    if row["pid"].startswith("P") and not repo_name.startswith(row["pid"].lower()):
        flags.append("NAME_NOT_NUMBERED")

    dirty = git(path, "status", "--porcelain").stdout.strip()
    facts["dirty"] = len(dirty.splitlines()) if dirty else 0
    if facts["dirty"]:
        flags.append("DIRTY_WORKTREE")

    if git(path, "rev-parse", "--abbrev-ref", "@{upstream}").returncode != 0:
        flags.append("NO_UPSTREAM")
        return flags, facts
    if fetch:
        git(path, "fetch", "--prune", "--quiet")
    ab = git(path, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").stdout.split()
    facts["ahead"], facts["behind"] = (int(ab[0]), int(ab[1])) if len(ab) == 2 else ("?", "?")
    if facts["ahead"]:
        flags.append("UNPUSHED_COMMITS")
    if facts["behind"]:
        flags.append("BEHIND_REMOTE")
    return flags, facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", dest="mapfile")
    ap.add_argument("--root", default="/Users/zzymima0000/Developer/coding/1.Active")
    ap.add_argument("--fetch", action="store_true", help="git fetch --prune before ahead/behind")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    mapfile = os.path.abspath(a.mapfile or os.path.join(here, "..", "PROJECT_MAP.tsv"))
    if not os.path.isfile(maptopath := mapfile):
        print(f"ERROR: map not found: {mapfile}", file=sys.stderr)
        return 2

    rows = read_map(mapfile)
    seen = {}
    results, problems = [], 0
    for row in rows:
        flags, facts = audit_row(row, a.root, a.fetch)
        if row["repo"] and row["kind"] != "orphan":
            seen.setdefault(row["repo"], []).append(row["pid"])
        results.append({"pid": row["pid"], "kind": row["kind"], "name": row["display_name"],
                        "flags": flags, "facts": facts})
        if flags:
            problems += 1
    dupes = {r: p for r, p in seen.items() if len(p) > 1}
    for res in results:
        for r, p in dupes.items():
            if res["facts"].get("repo") == r and "DUPLICATE_MAPPING" not in res["flags"]:
                res["flags"].append("DUPLICATE_MAPPING")
                problems += 1

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for res in results:
            f = res["facts"]
            head = f"{res['pid'] or '-'}  {res['name']}"
            print(head)
            print(f"  Local:    {f.get('local', f.get('error', 'n/a'))}")
            print(f"  Repo:     {f.get('repo', '-')} ({f.get('visibility', '-')})")
            print(f"  Origin:   {f.get('origin', '-')}")
            print(f"  Branch:   {f.get('branch', '-')}  upstream→{f.get('ahead', '-')} ahead / {f.get('behind', '-')} behind")
            print(f"  Dirty:    {'YES' if f.get('dirty') else 'NO'} ({f.get('dirty', 0)} paths)")
            if f.get("no_backup_check"):
                print("  Backup:   N/A (未绑定本地项目)")
            else:
                print(f"  Backup:   {'COMPLETE' if not (set(res['flags']) & {'DIRTY_WORKTREE', 'UNPUSHED_COMMITS', 'NO_ORIGIN', 'NOT_GIT', 'REMOTE_NOT_FOUND', 'NO_UPSTREAM'}) else 'INCOMPLETE'}")
            print(f"  Status:   {', '.join(res['flags']) if res['flags'] else 'OK'}")
            print()
        ok = sum(1 for r in results if not r["flags"])
        print(f"Scanned {len(results)} entries · clean {ok} · with findings {problems}")
    return 1 if problems else 2 if not results else 0


if __name__ == "__main__":
    sys.exit(main())
