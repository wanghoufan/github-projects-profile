#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GitHub 项目全景材料（给智能体的背景档案）。

设计目标：可迁移、跨平台（macOS / Linux / Windows 11）、可被其他智能体复用。
- 不写死任何绝对路径：用户名自动探测，输出路径用 ~ 展开 / 环境变量覆盖。
- 输出文件强制 UTF-8；Windows 终端默认 cp936，启动时 reconfigure stdout/stderr 为 UTF-8。

前置条件：
- 本机 `gh` 已登录，且 token 含 `repo` 权限（否则私有仓库不可见）。验证：gh auth status
- python3 可用（macOS/Linux 自带；Windows 装 Python 3.9+ 并加入 PATH）

用法：
  python3 scripts/generate_portfolio.py
  默认输出：~/.workbuddy/GITHUB_PROJECTS.md
  覆盖输出：PORTFOLIO_OUT=/abs/path/out.md python3 scripts/generate_portfolio.py
  指定账号：PORTFOLIO_USER=otherlogin python3 scripts/generate_portfolio.py

逻辑：
  1. gh repo list 拉取当前用户全部仓库（公开+私有）；
  2. 逐仓库用 gh api 取 README（base64）与最近一次 commit；
  3. 从 README 提炼「功能 / 技术栈 / 最新进度」；
  4. 按主题分组渲染成 Markdown，写入输出文件。
"""
from __future__ import annotations

import json
import subprocess
import base64
import re
import os
import sys
import time
from datetime import date

# Windows 终端默认 codepage 为 cp936，中文 print 易触发 UnicodeEncodeError。
# 启动时把 stdout/stderr 重配置为 UTF-8（仅当 API 可用）。
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def detect_user() -> str:
    """目标 GitHub 用户：优先环境变量，其次当前 gh 登录账号。"""
    env = os.environ.get("PORTFOLIO_USER")
    if env:
        return env
    try:
        r = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    # 不写死任何账号名：探测失败就明确报错，避免把机器专属账号写进可迁移脚本。
    raise SystemExit("无法识别 GitHub 账号，请先执行 gh auth login，或设置 PORTFOLIO_USER。")


USER = detect_user()
# 输出位置：默认用户级私有目录（~ 在 macOS/Windows 均有效），可用环境变量覆盖。
OUT = os.environ.get(
    "PORTFOLIO_OUT",
    os.path.expanduser("~/.workbuddy/GITHUB_PROJECTS.md"),
)


# GitHub API 偶发网络抖动（EOF / timeout / connection reset），属可重试错误，
# 不是鉴权失败。命中这些关键词时自动退避重试，避免误判为「gh 未登录」。
RETRYABLE = re.compile(r"EOF|timeout|timed out|connection reset|i/o timeout|TLS|no such host", re.I)


def gh(args, retries=2):
    for attempt in range(retries + 1):
        r = subprocess.run(["gh"] + args, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        err = (r.stderr or "")[:400]
        if attempt < retries and RETRYABLE.search(err):
            sys.stderr.write("gh 网络抖动，重试 %d/%d: %s\n" % (attempt + 1, retries, " ".join(args)[:80]))
            time.sleep(1.5 * (attempt + 1))
            continue
        sys.stderr.write("gh failed: " + " ".join(args) + "\n" + err + "\n")
        return None
    return None


def clean(t):
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"`", "", t)
    t = re.sub(r"\*{1,3}", "", t)  # 去掉 markdown 加粗标记，便于噪声识别
    t = re.sub(r"\s+", " ", t).strip(" -*>")
    return t.strip()


# 从 README 段落里抓到的「噪声行」：表格残片、安装/启动命令、代码注释等。
# 这些不是功能或技术栈描述，必须剔除，否则材料里会出现 "npm install" "| 包 | 用途 |" 这类内容。
def is_noise(s):
    s = (s or "").strip()
    if not s:
        return True
    if s.startswith("|") or s.startswith("---") or set(s) <= set("-:=| *"):
        return True
    # 命令行：包管理器 + 子命令（npm install / pnpm add / docker compose up …）。
    # 只对「工具 + 动词」判噪，避免把 "Python 3 静态站点生成器" 这类以语言名开头的正常描述误杀。
    if re.match(r"^(npm|pnpm|yarn|bun|npx|pip3?|poetry|uv|cargo|go|mvn|gradle|docker|"
                r"docker-compose|git)\s+(install|i|add|run|dev|build|start|ci|clone|"
                r"checkout|up|compose|exec|serve|deploy|test|migrate)\b", s, re.I):
        return True
    if re.match(r"^(cd|make|sudo|\./)\s", s, re.I):
        return True
    if re.match(r"^(python3?|node)\s+(-\S+\s+)*\S+\.(py|js|mjs|sh)\b", s, re.I):
        return True
    if re.match(r"^(#|//|/\*|--)\s", s):
        return True
    if any(w in s for w in ("安装依赖", "装依赖", "管理依赖", "依赖安装", " install", " clone",
                            " 安装 ", "启动项目", "快速开始", "环境要求")):
        return True
    return False


def get_section(readme, keys, max_items=6):
    if not readme:
        return []
    lines = readme.splitlines()
    capture = False
    buf = []
    for l in lines:
        if re.match(r"^#{1,6}\s", l):
            if any(k in l.lower() for k in keys):
                capture = True
                continue
            elif capture:
                break
        if capture:
            s = l.strip()
            if not s:
                continue
            item = None
            if re.match(r"^[-*]\s", s) or re.match(r"^\d+[.)]\s", s):
                item = re.sub(r"^([-*\d.)]\s)+", "", s).strip()
            elif len(buf) < 2 and not re.match(r"^[>#`]", s):
                item = s
            if item:
                # 边收边过滤：噪声行不占位，避免它们挤掉后面真正的技术栈 / 功能条目。
                ci = clean(item)
                if ci and not is_noise(ci):
                    buf.append(ci)
            if len(buf) >= max_items:
                break
    return buf[:max_items]


# 「最新进度」两轮匹配：
#   第一轮（强匹配）：行首就是「状态/进度：」这类明确的状态行，最可信；
#   第二轮（弱匹配）：只在行内含状态关键词且长度合理时命中，避免抓到 README 中间的随机条目。
STRONG_STATUS = re.compile(
    r"^[->*\s]*(当前状态|项目状态|开发状态|当前进度|状态|进度|Status)\*{0,2}\s*[:：]", re.I)
WEAK_STATUS = ("当前状态", "项目状态", "状态：", "进度：", "在役", "已完成", "进行中",
               "DONE", "roadmap", "changelog", "更新日志", "最新更新")


def get_status(readme, last_commit, updated):
    if readme:
        lines = [l.strip() for l in readme.splitlines()]
        for l in lines:
            if not l or l.startswith("#") or l.startswith("|"):
                continue
            c = clean(l)
            if not c:
                continue
            if STRONG_STATUS.search(c):
                c = re.sub(STRONG_STATUS.pattern, "", c, flags=re.I).strip()
                if 4 < len(c) < 160:
                    return c
        for l in lines:
            if not l or l.startswith("#") or l.startswith("|"):
                continue
            c = clean(l)
            if not c:
                continue
            if any(k.lower() in c.lower() for k in WEAK_STATUS):
                if 8 < len(c) < 160:
                    return c
    if last_commit:
        return "最近提交：" + last_commit
    return "—"


# 主题分组：迁移到别的账号时替换这里的仓库名即可。
# 维护原则：新仓库出现后应及时归入已有组或新建组，避免全部掉进「其他 / 未分类」（该组堆积会稀释分类价值）。
GROUPS = [
    ("语音 / 输入工具", ["landedazi-android", "no-more-typing"]),
    ("ORCA / 治理 / 基础设施", ["orca-deepseek-bridge", "orca-governance-validation-progress",
                          "orca-v2.1-governance"]),
    ("额度 / 汇率桌面组件", ["DeepSeekBalanceWidget-Windows", "DeepSeekBalanceWidget-Mac",
                        "cny-us-rate-board", "cny-rate-board"]),
    ("加密 / 行情研判", ["pepe-doge-breakout-radar-deepseek-v4-pro",
                    "pepe-doge-breakout-radar-KIMI-K2.7-CODE"]),
    ("金融 / 投资看板", ["family-insurance-dashboard", "a-share-index-valuation-report",
                   "roll-position-calculator", "hongli-dixin-calc"]),
    ("个人记录 / PWA", ["place-journal", "personal-rss"]),
    ("摄影", ["photo-library", "photo-spot-app"]),
    ("AI 工具 / 求职 / 测试", ["ai-resume-job-matcher", "ai-storyboard-generator",
                          "life-species-coze-v1.3", "24-species-test"]),
    ("个人网站 / 作品集", ["houfan-xuezhang-site", "personal-website", "nomad-seasons"]),
    ("健康 / 运动工具", ["stretch-routine-app", "stretch-side-timer-project",
                   "stretch-side-timer", "protein-calculator"]),
    ("视频 / 笔记转写", ["Video2Obsidian-Windows", "Video2Obsidian-Mac"]),
    ("MCP / 自动化 / Skills / 数据库治理", ["prompt-manager", "skills-manager-backup",
                                  "dida365-workbuddy-time-system", "workbuddy-dual-axis-tutorial",
                                  "alw-db-governance"]),
    ("生活 / 实用小工具", ["qinyuan-tupu", "yejian-buguangdeng", "party-night-v1-2",
                    "50-haikou-cafes"]),
]
group_of = {}
for g, names in GROUPS:
    for n in names:
        group_of[n] = g


def grp(name):
    return group_of.get(name, "其他 / 未分类")


# 人工补写的定位（覆盖 API 空描述 / 私有库无描述），保证材料可读。
# 迁移到其他账号时，可整体替换为目标账号的仓库名 -> 定位。
DESCRIPTION_OVERRIDE = {
    "personal-website": "个人网站（Next.js 16 + shadcn/ui 全栈应用，由扣子编程 CLI 创建）。",
    "cny-rate-board": "Windows 桌面 USD/CNY 汇率毛玻璃悬浮窗：多周期区间统计 + 美元贵贱档位（不画走势图）。",
    "qinyuan-tupu": "亲缘图谱 · 中文家庭关系与称谓计算工具（纯前端 SPA，代际分层图谱可视化）。",
    "orca-governance-validation-progress": "ORCA 治理校验归档仓：归档治理交接、运行时调查证据与 Level 3 冻结状态（不含模板源树）。",
    "alw-db-governance": "alw丨数据库管理专家：共享 Supabase 数据库的公共治理中心（接入规范 / 方案审查 / Migration）。",
    "orca-deepseek-bridge": "ORCA DeepSeek Bridge：ORCA 经薄桥接层直连 DeepSeek 官方 ACP/API 的可复用基础设施（Phase 1 MVP 完成）。",
    "Video2Obsidian": "Video2Obsidian｜本地视频自动转写写入 Obsidian 工具（本地 Whisper，零 API 成本，Apple Silicon Mac）。",
    "personal-rss": "personal-rss：基于 FreshRSS + RSSHub + Redis 的个人信息雷达 RSS 聚合（Docker 部署工作区）。",
    "24-species-test": "（空仓库，暂无 README / 内容）。",
}

# 超过该天数未更新视为「长期停滞」，在材料中标红提示。
STALE_DAYS = 30


def main():
    print("== 拉取仓库清单（含私有）==")
    out = gh(["repo", "list", "--limit", "200",
              "--json", "name,visibility,updatedAt,description,primaryLanguage,homepageUrl,url,stargazerCount"])
    if not out:
        sys.exit("无法获取仓库列表（已自动重试网络抖动仍失败）。请确认 gh 已登录（gh auth status）、"
                 "token 含 repo 权限，或稍后再试。")
    repos = json.loads(out)
    for r in repos:
        r["visibility"] = (r.get("visibility") or "").lower()
    print("仓库总数:", len(repos), "｜ 目标用户:", USER)

    results = []
    for r in repos:
        name = r["name"]
        entry = dict(name=name, visibility=r["visibility"], updatedAt=r["updatedAt"],
                     description=r.get("description"),
                     language=(r.get("primaryLanguage") or {}).get("name"),
                     homepage=r.get("homepageUrl"), url=r.get("url"), stars=r.get("stargazerCount"),
                     readme=None, last_commit=None)
        raw = gh(["api", f"repos/{USER}/{name}/readme", "--jq", ".content"])
        if raw and raw.strip():
            try:
                entry["readme"] = base64.b64decode(raw).decode("utf-8", "replace")
            except Exception:
                pass
        cm = gh(["api", f"repos/{USER}/{name}/commits?per_page=1", "--jq", ".[0].commit.message"])
        if cm:
            entry["last_commit"] = cm.strip().split("\n")[0][:140]
        results.append(entry)

    by_name = {r["name"]: r for r in results}
    ordered = sorted(results, key=lambda r: r["updatedAt"], reverse=True)
    pub = sum(1 for r in results if r["visibility"] == "public")
    pri = sum(1 for r in results if r["visibility"] == "private")
    today = date.today()

    md = []
    md.append("# 我的 GitHub 项目全景（给智能体的背景档案）\n")
    md.append("> 自动采集自 GitHub API（本机 `gh` 鉴权，含私有仓库）。用途：让智能体快速熟悉你正在开发的项目、技术栈与进度，从而给出更针对性的建议。\n")
    md.append("> 生成时间：%s ｜ 目标用户：%s ｜ 仓库总数：**%d**（公开 %d / 私有 %d）\n" % (
        today.isoformat(), USER, len(results), pub, pri))
    md.append("\n## 总览（按最近更新排序）\n")
    md.append("| 项目 | 类型 | 语言 | 最近更新 | 一句话定位 |")
    md.append("|---|---|---|---|---|")
    for r in ordered:
        desc = DESCRIPTION_OVERRIDE.get(r["name"]) or clean(r["description"]) or "(无描述)"
        if len(desc) > 38:
            desc = desc[:37] + "…"
        md.append("| `%s` | %s | %s | %s | %s |" % (
            r["name"], "公开" if r["visibility"] == "public" else "**私有**",
            r["language"] or "—", r["updatedAt"][:10], desc))

    stale_list = [r for r in results if (today - date.fromisoformat(r["updatedAt"][:10])).days >= STALE_DAYS]
    if stale_list:
        stale_list.sort(key=lambda r: r["updatedAt"])
        md.append("\n## ⚠️ 长期未更新（≥%d 天未提交）\n" % STALE_DAYS)
        for r in stale_list:
            sd = (today - date.fromisoformat(r["updatedAt"][:10])).days
            md.append("- `%s` · %s · 最近更新 %s（%d 天前）" % (
                r["name"], "公开" if r["visibility"] == "public" else "私有", r["updatedAt"][:10], sd))

    md.append("\n---\n")
    md.append("## 分主题详情\n")

    def render_entry(r):
        rm = r.get("readme")
        feats = get_section(rm, ["功能", "特性", "feature", "functions", "能力", "what it"])
        tech = get_section(rm, ["技术栈", "技术", "tech", "stack", "依赖", "built with", "架构"])
        status = get_status(rm, r.get("last_commit"), r["updatedAt"])
        days = (today - date.fromisoformat(r["updatedAt"][:10])).days
        stale = "  ⚠️ 已 %d 天未更新（长期停滞）" % days if days >= STALE_DAYS else ""
        lines = []
        lines.append("\n#### `%s`  ·  %s\n" % (r["name"], "公开" if r["visibility"] == "public" else "私有"))
        lines.append("- **定位**：%s" % (DESCRIPTION_OVERRIDE.get(r["name"]) or clean(r["description"]) or "(无描述)"))
        lines.append("- **链接**：%s ｜ 预览：%s ｜ 语言：%s ｜ 更新：%s ｜ Stars：%s" % (
            r["url"], r["homepage"] or "—", r["language"] or "—", r["updatedAt"][:10], r["stars"]))
        lines.append("- **功能**：" + ("；".join(feats) if feats else "（README 未列明要点，详见上方链接）"))
        if tech:
            lines.append("- **技术栈**：" + "；".join(tech))
        elif r["language"]:
            lines.append("- **技术栈**：%s（详见 README）" % r["language"])
        else:
            lines.append("- **技术栈**：（详见 README）")
        lines.append("- **最新进度**：%s；%s%s" % (r["updatedAt"][:10], status, stale))
        return lines

    for g, names in GROUPS:
        md.append("\n### %s\n" % g)
        for n in names:
            r = by_name.get(n)
            if not r:
                continue
            md.extend(render_entry(r))

    uncat = [r for r in results if grp(r["name"]) == "其他 / 未分类"]
    if uncat:
        md.append("\n### 其他 / 未分类\n")
        for r in uncat:
            md.extend(render_entry(r))
        # 未分类堆积说明 GROUPS 需要维护（新仓库未归类），显式提示便于及时补录。
        if len(uncat) > 5:
            sys.stderr.write("提示：有 %d 个仓库落入「其他 / 未分类」，建议在 GROUPS 中补充分组：%s\n"
                             % (len(uncat), ", ".join(r["name"] for r in uncat)))

    out_dir = os.path.dirname(OUT)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("WRITTEN", OUT, "chars:", len("\n".join(md)))


if __name__ == "__main__":
    main()
