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
  默认输出：~/.workbuddy/GITHUB_PROJECTS.md 与 ~/.workbuddy/SKILL_CONTEXT.md（同目录两份）
  覆盖输出：PORTFOLIO_OUT=/abs/path/out.md python3 scripts/generate_portfolio.py
  单独指定第二份：SKILL_CONTEXT_OUT=/abs/path/SKILL_CONTEXT.md python3 scripts/generate_portfolio.py
  指定账号：PORTFOLIO_USER=otherlogin python3 scripts/generate_portfolio.py
  离线调试：PORTFOLIO_DUMP_JSON=/tmp/raw.json python3 scripts/generate_portfolio.py（存采集结果）

逻辑：
  1. gh repo list 拉取当前用户全部仓库（公开+私有）；
  2. 逐仓库用 gh api 取 README（base64）与最近一次 commit；
  3. 从 README 提炼「功能 / 技术栈 / 最新进度」；
  4. 按主题分组渲染成 Markdown，写入 GITHUB_PROJECTS.md；
  5. 用同一份采集结果，经 scripts/skill_context.py 的确定性规则派生
     SKILL_CONTEXT.md（Skill 日报用的轻量需求画像）——不二次请求 API、不调用大模型。

退出码：0 正常；1 = 有仓库 README/提交没拉到（文件仍写出，但显式标记失败）；2 = 仓库列表都没拉到。
"""
from __future__ import annotations

import json
import subprocess
import base64
import re
import os
import sys
import time
from datetime import date, datetime

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


def now_stamp() -> str:
    """生成时间戳（YYYY-MM-DD HH:mm）。时区由运行环境决定：
    本地运行取本机时区，CI 运行统一设 TZ=Asia/Shanghai。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# GitHub API 偶发网络抖动（EOF / timeout / connection reset），属可重试错误，
# 不是鉴权失败。命中这些关键词时自动退避重试，避免误判为「gh 未登录」。
NET_HINT = re.compile(r"EOF|timeout|timed out|connection reset|i/o timeout|TLS|no such host", re.I)
RETRYABLE = NET_HINT


def detect_user() -> str:
    """目标 GitHub 用户：优先环境变量，其次当前 gh 登录账号。

    这里自带网络抖动重试：探测失败必须区分「网络问题」与「未登录」——
    实测 gh 偶发 EOF 时若直接报「请先 gh auth login」，排查方向会被彻底带偏。
    """
    env = os.environ.get("PORTFOLIO_USER")
    if env:
        return env
    err = ""
    for attempt in range(3):
        try:
            r = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True, text=True,
            )
        except Exception as exc:  # gh 不存在 / 无法执行
            raise SystemExit("无法执行 gh（%s）。请先安装 GitHub CLI：https://cli.github.com/" % exc)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        err = (r.stderr or "").strip()
        if attempt < 2 and NET_HINT.search(err):
            sys.stderr.write("gh 网络抖动，重试账号探测 %d/2\n" % (attempt + 1))
            time.sleep(1.5 * (attempt + 1))
            continue
        break
    reason = (err.splitlines()[0] if err else "(gh 无错误输出)")
    # 不写死任何账号名：探测失败就明确报错，避免把机器专属账号写进可迁移脚本。
    raise SystemExit(
        "无法识别 GitHub 账号。原因：%s\n"
        "  排查顺序：1) 若是网络类报错（EOF/timeout/connection reset），直接重跑即可；"
        "2) gh auth status 确认已登录且令牌含 repo 权限（否则看不到私有仓库）；"
        "3) 也可用 PORTFOLIO_USER=账号名 显式指定。" % reason)


USER = detect_user()
# 输出位置：默认用户级私有目录（~ 在 macOS/Windows 均有效），可用环境变量覆盖。
OUT = os.environ.get(
    "PORTFOLIO_OUT",
    os.path.expanduser("~/.workbuddy/GITHUB_PROJECTS.md"),
)


# 采集诊断：用于运行日志里区分「正常情况」与「真失败」，避免静默失败。
# 键：retry 网络抖动重试次数 / empty 空仓库、无 README（正常）/ readme_fail、commit_fail 真失败。
DIAG = {"retry": 0, "empty": [], "readme_fail": [], "commit_fail": []}
LAST_ERR = ""


def gh(args, retries=2):
    global LAST_ERR
    for attempt in range(retries + 1):
        r = subprocess.run(["gh"] + args, capture_output=True, text=True)
        if r.returncode == 0:
            LAST_ERR = ""
            return r.stdout
        err = (r.stderr or "")[:400]
        LAST_ERR = err
        if attempt < retries and RETRYABLE.search(err):
            DIAG["retry"] += 1
            sys.stderr.write("gh 网络抖动，重试 %d/%d: %s\n" % (attempt + 1, retries, " ".join(args)[:80]))
            time.sleep(1.5 * (attempt + 1))
            continue
        sys.stderr.write("gh failed: " + " ".join(args) + "\n" + err + "\n")
        return None
    return None


def last_err_brief():
    """取最近一次 gh 失败信息的一行摘要，用于日志里定位失败原因。"""
    for line in (LAST_ERR or "").splitlines():
        line = line.strip()
        if line:
            return line[:160]
    return "(无错误输出)"


def is_empty_repo_error():
    """空仓库 / 无 README 属于正常情况（不是鉴权或权限问题）。

    - `readme` 接口在无 README 或空仓库上返回 404 Not Found；
    - `commits` 接口在空仓库上返回 409 Git Repository is empty。
    """
    e = LAST_ERR or ""
    return ("Not Found" in e) or ("is empty" in e) or ("404" in e) or ("409" in e)


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
    "github-projects-profile": "本仓：GitHub 项目全景档案 + Skill 推荐背景，两份 Markdown 由脚本每日自动生成，供智能体读取。",
}

# 超过该天数未更新视为「长期停滞」，在材料中标红提示。
STALE_DAYS = 30

# §6 内外分层：Public 档案默认只渲染公开仓库。私有仓库的名称、描述、README 摘要与进度
# 属于内部注册表（../000-alw-steward 内部治理/PROJECT_MAP.tsv），不出现在公开仓。
# 需要旧行为时显式 PORTFOLIO_PRIVATE_DETAIL=1。
PUBLIC_ONLY = os.environ.get("PORTFOLIO_PRIVATE_DETAIL", "0") != "1"

# README 分段提取的标题关键词（同时供 SKILL_CONTEXT 派生信号复用，勿在此之外另写一份）。
FEATURE_KEYS = ["功能", "特性", "feature", "functions", "能力", "what it"]
TECH_KEYS = ["技术栈", "技术", "tech", "stack", "依赖", "built with", "架构"]

# 内容（忽略生成时间戳）没变时不重写文件，从根上避免「每日空 commit」。
SKIP_IF_UNCHANGED = os.environ.get("PORTFOLIO_WRITE_ALWAYS", "").strip() not in ("1", "true", "TRUE")


def load_skill_context():
    """加载同目录下的确定性生成模块（scripts/skill_context.py）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import skill_context
    except ImportError as exc:
        sys.exit("生成 SKILL_CONTEXT.md 失败：无法导入 scripts/skill_context.py（%s）" % exc)
    return skill_context


def main():
    # 前置检查：生成模块必须先能导入，避免采集 1 分钟后再失败。
    sc = load_skill_context()
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
        if raw is None:
            if is_empty_repo_error():
                DIAG["empty"].append(name)
            else:
                DIAG["readme_fail"].append((name, last_err_brief()))
        elif raw.strip():
            try:
                entry["readme"] = base64.b64decode(raw).decode("utf-8", "replace")
            except Exception as exc:
                DIAG["readme_fail"].append((name, "README base64 解码失败: %s" % exc))
        cm = gh(["api", f"repos/{USER}/{name}/commits?per_page=1", "--jq", ".[0].commit.message"])
        if cm:
            entry["last_commit"] = cm.strip().split("\n")[0][:140]
        elif not is_empty_repo_error():
            DIAG["commit_fail"].append((name, last_err_brief()))
        # 供 SKILL_CONTEXT 派生使用的「声明式信号」：与上面档案同一套分段提取逻辑，
        # 只吃项目自己声明的功能/技术栈，避免把 README 正文里的偶然提及当成技术栈。
        entry["signal_feats"] = get_section(entry["readme"], FEATURE_KEYS)
        entry["signal_tech"] = get_section(entry["readme"], TECH_KEYS)
        results.append(entry)

    # 采集诊断：必须能从日志区分「鉴权/权限失败」「README 失败」「正常空仓库」。
    ok_readme = sum(1 for r in results if r.get("readme"))
    print("== 采集诊断 ==")
    print("  仓库 %d ｜ 取到 README %d ｜ 空仓库/无 README（正常）%d ｜ 网络抖动重试 %d"
          % (len(results), ok_readme, len(DIAG["empty"]), DIAG["retry"]))
    if DIAG["empty"]:
        print("  正常空仓库 / 无 README：%s" % ", ".join(DIAG["empty"]))
    for key, label in (("readme_fail", "README 拉取失败"), ("commit_fail", "最近提交拉取失败")):
        if DIAG[key]:
            print("  ERROR: %s %d 个" % (label, len(DIAG[key])))
            for name, why in DIAG[key]:
                print("    - %s：%s" % (name, why))
            if any(("auth" in w.lower() or "403" in w or "401" in w) for _n, w in DIAG[key]):
                print("  ERROR 提示：疑似鉴权或私有仓库权限不足，请检查 token 是否含 repo 权限。")
    if not DIAG["readme_fail"] and not DIAG["commit_fail"]:
        print("  无拉取失败。")

    # 采集结果落盘（可选）：离线调试 / 复盘渲染逻辑时不必再打一遍 GitHub API。
    # 只在显式设置 PORTFOLIO_DUMP_JSON 时写，日常运行不产生额外文件。
    dump = os.environ.get("PORTFOLIO_DUMP_JSON")
    if dump:
        with open(os.path.expanduser(dump), "w", encoding="utf-8") as f:
            json.dump({"user": USER, "collected_at": now_stamp(), "repos": results},
                      f, ensure_ascii=False, indent=1)
        print("DUMPED", dump)

    all_repos = results
    hidden = [r for r in all_repos if r["visibility"] != "public"] if PUBLIC_ONLY else []
    if PUBLIC_ONLY:
        results = [r for r in all_repos if r["visibility"] == "public"]
    by_name = {r["name"]: r for r in results}
    ordered = sorted(results, key=lambda r: r["updatedAt"], reverse=True)
    pub = sum(1 for r in all_repos if r["visibility"] == "public")
    pri = sum(1 for r in all_repos if r["visibility"] != "public")
    today = date.today()

    md = []
    md.append("# 我的 GitHub 项目全景（给智能体的背景档案）\n")
    md.append("> 自动采集自 GitHub API。本文件是 Public 展示层：只列公开仓库；"
              "私有仓库明细在内部注册表，不在此输出。\n")
    # §8：公开层不输出精确私有数量，避免每新增一个内部仓就产生无意义 diff
    md.append("> 生成时间：%s ｜ 目标用户：%s ｜ 公开仓库：**%d**\n" % (
        today.isoformat(), USER, pub))
    if hidden:
        md.append("> 另有私有仓库未在本文件列出（名称、描述与进度均属内部治理层，不公开）。\n")
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
        feats = get_section(rm, FEATURE_KEYS)
        tech = get_section(rm, TECH_KEYS)
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
    portfolio_text = "\n".join(md) + "\n"
    changed_p = sc.write_if_changed(OUT, portfolio_text, SKIP_IF_UNCHANGED)
    print("%s %s ｜ 字符数: %d" % ("WRITTEN" if changed_p else "UNCHANGED", OUT, len(portfolio_text)))

    # ---- 第二份文件：Skill 需求画像 ----
    # 与上面同一份采集结果派生：不重复请求 GitHub API、不调用任何大模型。
    # 默认与 GITHUB_PROJECTS.md 放同一目录，可用 SKILL_CONTEXT_OUT 单独覆盖。
    skill_out = os.environ.get("SKILL_CONTEXT_OUT") or os.path.join(
        os.path.dirname(OUT) or ".", "SKILL_CONTEXT.md")
    prev_text = sc.read_text(skill_out)

    try:
        skill_text = sc.build_skill_context(
            results, desc_override=DESCRIPTION_OVERRIDE, today=today,
            prev_text=prev_text, updated_at=now_stamp())
    except Exception as exc:
        sys.exit("生成 SKILL_CONTEXT.md 失败：%s: %s" % (type(exc).__name__, exc))

    changed_s = sc.write_if_changed(skill_out, skill_text, SKIP_IF_UNCHANGED)
    print("%s %s ｜ 字符数: %d ｜ 相对完整档案体积: %.0f%%（%d → %d 字符）"
          % ("WRITTEN" if changed_s else "UNCHANGED", skill_out, len(skill_text),
             100.0 * len(skill_text) / max(len(portfolio_text), 1),
             len(portfolio_text), len(skill_text)))
    if not changed_p and not changed_s:
        print("两份文件内容均无实质变化（生成时间戳不算变化），无需提交。")

    # 退出码：0 正常；1 = 有仓库内容没拉到（文件仍写出，但运行状态标记为失败，不静默）；
    # 2 = 完全没拿到仓库列表（见 main 开头 sys.exit）。
    if DIAG["readme_fail"] or DIAG["commit_fail"]:
        sys.stderr.write("ERROR: 本次采集存在拉取失败项，内容可能不完整（详见上方诊断）。\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
