#!/usr/bin/env python3
"""Render PROJECT_MAP.tsv (+ audit JSON) into PROJECT_MAP.md, the mapping SSOT view."""
import argparse
import json
import os
from datetime import date

COLS = ["pid", "kind", "local_path", "display_name", "repo", "visibility", "note"]
HERE = os.path.dirname(os.path.abspath(__file__))


def read_map(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        assert header == COLS, f"unexpected header: {header}"
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            parts += [""] * (len(COLS) - len(parts))
            rows.append(dict(zip(COLS, parts)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=os.path.join(HERE, "..", "..", "000-alw-steward 内部治理", "PROJECT_MAP.tsv"))
    ap.add_argument("--audit", default="/tmp/audit.json")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "000-alw-steward 内部治理", "PROJECT_MAP.md"))
    ap.add_argument("--today", default=date.today().isoformat())
    a = ap.parse_args()

    facts = {}
    if os.path.isfile(a.audit):
        for entry in json.load(open(a.audit, encoding="utf-8")):
            key = entry["facts"].get("repo") or entry["name"]
            facts[key] = entry
            facts[entry["name"]] = entry

    rows = read_map(os.path.abspath(a.map))
    projects = [r for r in rows if r["kind"] == "project"]
    others = [r for r in rows if r["kind"] != "project"]

    out = ["# 项目映射表（Project ID SSOT）", "",
           f"> 由 `scripts/render_project_map.py` 生成于 {a.today}，数据源 `PROJECT_MAP.tsv`。",
           "> 本仓是项目总目录，不是第二份源码仓库：这里只记录名称、编号、映射与状态，不记录代码副本、密钥或 `.env`。",
           "",
           "## 编号规则",
           "",
           "- Project ID `PNNN` 与本地目录三位编号永久一致，状态由 `ing` 变 `done` 时不变。",
           "- 本地目录保留中文与状态：`NNN-状态-中文名`，面向人。",
           "- GitHub 仓库统一 `pNNN-english-slug`，不含 ing/done，不含版本号，面向互联网。",
           "- 一个项目只有一个主仓库；Public / Private 只是可见性属性，不为展示复制第二份代码。",
           "- 真正独立发布的多平台仓库共用一个 Project ID，加角色后缀（如 `-mac` / `-windows`）。",
           "- `000-*` 是基础设施目录，暂不纳入 P 编号。",
           "",
           "## 一览表",
           "",
           "| Project ID | 本地目录 | GitHub Repo | 可见性 | 生命周期 | Backup | 结论 |",
           "|---|---|---|---|---|---|---|"]

    def cell(r):
        f = facts.get(r["repo"] or r["display_name"], facts.get(r["display_name"], {}))
        fl = f.get("flags", [])
        vis = f.get("facts", {}).get("visibility", r["visibility"]) or "-"
        dirty = f.get("facts", {}).get("dirty")
        ahead = f.get("facts", {}).get("ahead", "-")
        behind = f.get("facts", {}).get("behind", "-")
        if r["kind"] == "orphan":
            backup = "n/a"
        elif fl and set(fl) & {"NOT_GIT", "NO_ORIGIN", "REMOTE_NOT_FOUND", "WRONG_OWNER"}:
            backup = "NONE"
        elif dirty or (isinstance(ahead, int) and ahead) or (isinstance(behind, int) and behind):
            backup = "PARTIAL"
        else:
            backup = "COMPLETE"
        status = "OK" if not fl else ", ".join(fl)
        life = ""
        name = r["local_path"].split("/")[0] if r["local_path"] not in ("", "-") else "-"
        parts = name.split("-")
        if len(parts) > 1 and parts[1] in ("ing", "done", "alw"):
            life = parts[1]
        return (f"| {r['pid'] or '-'} | `{name}` | `{r['repo'] or '-'}` | {vis} | {life or '-'} "
                f"| {backup} | {status}{'; ' + r['note'] if r['note'] else ''} |")

    for r in projects:
        out.append(cell(r))
    out += ["", "## 000-* 基础设施 / 嵌套 / 外部 / 未绑定仓库", "",
            "| 类型 | 本地目录 | GitHub Repo | 可见性 | 结论 |", "|---|---|---|---|---|"]
    for r in others:
        f = facts.get(r["repo"] or r["display_name"], {})
        fl = f.get("flags", [])
        out.append(f"| {r['kind']} | `{r['local_path'] or '-'}` | `{r['repo'] or '-'}` "
                   f"| {r['visibility'] or f.get('facts', {}).get('visibility', '-') or '-'} "
                   f"| {'OK' if not fl else ', '.join(fl)}{'; ' + r['note'] if r['note'] else ''} |")

    out += ["", "## 标准档案字段（逐项目）", ""]
    for r in projects:
        f = facts.get(r["repo"] or r["display_name"], facts.get(r["display_name"], {}))
        fc = f.get("facts", {})
        top = r["local_path"].split("/")[0] if r["local_path"] not in ("", "-") else "-"
        parts = top.split("-")
        life = parts[1] if len(parts) > 1 and parts[1] in ("ing", "done") else "-"
        out += ["```text",
                f"Project ID: {r['pid']}",
                f"中文名: {r['display_name']}",
                f"本地目录: {top}",
                f"Git Root: {r['local_path']}",
                f"GitHub Repo: wanghoufan/{r['repo'] or '-'}",
                f"Visibility: {fc.get('visibility') or r['visibility'] or '-'}",
                f"Lifecycle: {life}",
                "Repo Role: main",
                f"Backup Status: {'OK' if not f.get('flags') else ', '.join(f.get('flags', [])) or 'OK'}",
                f"Dirty / Ahead / Behind: {fc.get('dirty', '-')} / {fc.get('ahead', '-')} / {fc.get('behind', '-')}",
                f"Last Verified: {a.today}",
                f"Note: {r['note'] or '-'}",
                "```", ""]

    with open(os.path.abspath(a.out), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {os.path.abspath(a.out)} ({len(projects)} projects, {len(others)} other entries)")


if __name__ == "__main__":
    main()
