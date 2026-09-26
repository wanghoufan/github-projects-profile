#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 GitHub 项目采集结果派生 `SKILL_CONTEXT.md`（Skill 推荐背景 / 需求画像）。

定位：
- `GITHUB_PROJECTS.md` = 完整项目档案（大，供深入判断单个项目）。
- `SKILL_CONTEXT.md`  = 轻量需求画像（小，供 Skill 日报 / 推荐智能体每天默认读取）。

设计约束（不可违背）：
- **不调用任何大模型 API**：全部由确定性 Python 规则完成归类与统计，同一份输入必得同一份输出。
- **不重复请求 GitHub API**：只吃 `generate_portfolio.py` 已采集好的结构化仓库数据。
- **不写死路径 / 账号 / 仓库名**：可整体复制到别的设备或别的账号使用。
- 仓库名、优先级都不写死：P0/P1/P2 由「活跃度加权得分 + 覆盖项目数」实时算出，
  同一份脚本在不同时间点跑出不同结论属于预期行为。

维护上手要点（改规则前先读这段）：
1. 三张规则表在文件顶部：`TECH`（技术栈）、`DEV_TYPES`（开发类型）、`NEEDS`（能力需求）。
   增删条目即可，不需要改渲染代码。
2. **命中强度**：项目自己声明的信息（仓库名 / 描述 / 主语言 / README 标题行 /
   README 的功能段与技术栈段）命中 1 次即算；只在 README 正文里出现的，技术栈要求
   ≥ `BODY_MIN_TECH` 次。这是为了防「治理文档里顺口提一句 Expo，整个仓库就被标成 RN 项目」。
3. **不要往正则里放「任何 README 都会出现」的词**（`compose`、`migration`、`bash`、
   `npm`、`windows 11`、泛称 `android`…），否则技术栈画像会整体失真。
   代码块会先被 `strip_code()` 剔除，所以 bash 命令、`npm install` 不会误触发。
4. **权重**：14 天内 ×3 / 30 天内 ×2 / 90 天内 ×1 / 更早 ×0.3。P0 还额外要求
   「14 天内活跃项目 ≥ `P0_MIN_HOT` 个」，避免只有老项目支撑的方向占据 P0。
5. **「最近变化」靠文件末尾的 `SKILL_CONTEXT_STATE` 注释块**：每次生成会写入本次的
   权重快照，下次生成时对比，差值 ≥ `REL_CHANGE` 才写进第 7 节。删掉那个块 = 重置基线。
"""
from __future__ import annotations

import json
import os
import re
from datetime import date

# 活跃度权重：近期真实需求优先，长期停滞的项目不参与决定 P0。
W_HOT = 3.0    # 0–14 天
W_ACTIVE = 2.0  # 15–30 天
W_WARM = 1.0   # 31–90 天
W_STALE = 0.3  # >90 天（仅用于保住长期基础设施的可见度，不足以撑起 P0）

HOT_DAYS = 14
ACTIVE_DAYS = 30
WARM_DAYS = 90

# 「命中强度」阈值：项目自己声明（仓库名/描述/标题/功能段/技术栈段）命中 1 次即算；
# 只在 README 正文里出现的，技术栈要求 ≥2 次（避免一次性提及被当成技术栈），
# 能力需求放宽到 1 次（需求是抽象判断，宁多勿漏）。
BODY_MIN_TECH = 3
BODY_MIN_NEED = 1

# P0 / P1 阈值：相对最高分归一化，避免仓库总量变化后阈值失效。
P0_RATIO = 0.45   # 得分 ≥ 最高分的 45%
P1_RATIO = 0.18
P0_MIN_HOT = 2    # 且至少 2 个 14 天内活跃的仓库（防止长期停滞项目独占 P0）
P0_MAX = 8        # P0 最多 8 条，避免清单膨胀
HOT_LIST_MAX = 30  # 「当前活跃项目」最多逐一列出多少个仓库（超出只给数量）
REL_CHANGE = 2.0  # 权重变化 ≥ 2.0 才写进「最近变化」

# ---------------------------------------------------------------- 技术栈规则
# (key, 显示名, 类别, 正则)
# 类别：通用 = 按得分分入「高频 / 中高频」；平台 / 基础设施 = 有命中即进「专项」。
# 维护原则：宁可漏判，不可误判。凡是「在任意 README 里都会出现」的词
# （compose、migration、bash、npm、windows 11、android 泛称…）一律不进正则，
# 否则每个仓库都会命中，技术栈画像立刻失真。
TECH = [
    ("typescript", "TypeScript", "通用", r"typescript|\.tsx?\b"),
    ("react", "React / Next.js", "通用", r"next\.js|nextjs|\breact\b"),
    ("python", "Python", "通用", r"\bpython\d?\b|python3|cpython"),
    ("node", "Node.js", "通用", r"node\.js|nodejs|node 2\d"),
    ("pwa", "PWA / 离线与本地存储", "通用",
     r"\bpwa\b|service worker|indexeddb|localstorage|local[- ]first|本地优先|离线优先|离线可用|离线继续"),
    ("llm", "LLM API（DeepSeek / 千问 / OpenAI…）", "通用",
     r"deepseek|openai|claude|qwen|百炼|dashscope|kimi|coze|gemini|大模型|\bllm\b|\bgpt\b|whisper"),
    ("tailwind", "Tailwind / shadcn", "通用", r"tailwind|shadcn"),
    ("playwright", "Playwright / 浏览器自动化", "通用", r"playwright|puppeteer|chromium"),
    ("expo", "Expo / React Native", "平台", r"\bexpo\b|react[- ]native|eas build"),
    ("supabase", "Supabase / Postgres", "基础设施",
     r"supabase|postgres|plpgsql|\brls\b|数据库迁移|migrations?/"),
    ("vercel", "Vercel / Netlify / CF Pages", "基础设施",
     r"vercel|netlify|cloudflare pages|github pages"),
    ("cloudflare", "Cloudflare", "基础设施", r"cloudflare|workers? kv|\br2\b"),
    ("docker", "Docker / 自托管", "基础设施", r"docker|自托管|self[- ]host|nginx"),
    ("kotlin", "Android / Kotlin", "平台", r"kotlin|\badb\b|gradle|android studio|jetpack"),
    ("swift", "macOS 桌面 / 原生", "平台", r"\bswift\b|macos|菜单栏|菜单条"),
    ("csharp", ".NET / C# / Windows 桌面", "平台", r"c#|\.net\b|wpf|winforms|winui"),
    ("rust", "Rust / Tauri", "平台", r"\brust\b|tauri|\bcargo\b"),
    ("shell", "Shell / 脚本", "通用", r"\bzsh\b|shell 脚本|命令行工具"),
    ("html-single", "单文件 HTML 工具", "平台",
     r"单文件 html|single[- ]file html|单页 html|单页响应式|离线 html"),
]

TECH_BY_KEY = {t[0]: t for t in TECH}

# 主语言直接作为技术栈信号（README 缺失时也能判断，且不会误判成别的栈）。
LANG_HINTS = {
    "TypeScript": "typescript",
    "Python": "python",
    "Kotlin": "kotlin",
    "Swift": "swift",
    "C#": "csharp",
    "Rust": "rust",
    "Shell": "shell",
    "PLpgSQL": "supabase",
    "Go": "shell",
}


# ---------------------------------------------------------------- 开发类型
# (显示名, 命中的技术栈 key) —— 用于「当前项目概况」
DEV_TYPES = [
    ("Web / PWA", ["react", "pwa", "html-single", "tailwind", "typescript"]),
    ("Expo / React Native", ["expo"]),
    ("Android", ["kotlin"]),
    ("macOS / 原生桌面", ["swift"]),
    (".NET / Windows 桌面", ["csharp"]),
    ("Python 自动化 / 数据处理", ["python"]),
    ("AI / Agent 工具", ["llm"]),
    ("数据库 / Supabase", ["supabase"]),
    ("部署 / 基础设施", ["vercel", "cloudflare", "docker"]),
    ("Rust / Tauri", ["rust"]),
    ("Shell / 系统脚本", ["shell"]),
]

# ---------------------------------------------------------------- 能力需求规则
# (key, 显示名, 正则, 英文搜索关键词, 影响说明)
# 这些是「抽象能力需求」，直接对应 Skill 类别，是 P0/P1/P2 与搜索词的来源。
NEEDS = [
    ("frontend-design", "UI / UX 设计、视觉与设计审查",
     r"界面|视觉|设计稿|ui/ux|\bui\b|\bux\b|组件库|tailwind|shadcn|审美|排版|间距|布局|交互",
     "frontend design ui review",
     "前端设计与设计审查类 Skill 权重上调"),
    ("browser-qa", "浏览器端 QA / E2E 自动化验证",
     r"playwright|e2e|端到端|冒烟|自动化测试|浏览器测试|截图验证|验收",
     "browser qa playwright e2e",
     "浏览器 QA / E2E 验证类 Skill 权重上调"),
    ("expo-rn", "Expo / React Native 开发与打包",
     r"\bexpo\b|react[- ]native|eas build|expo go",
     "expo react native",
     "移动端（React Native）开发与打包类 Skill 权重上调"),
    ("android", "Android 真机 QA / 构建签名",
     r"android|kotlin|\badb\b|gradle|真机",
     "android testing adb",
     "Android 构建与真机 QA 类 Skill 权重上调"),
    ("desktop-app", "桌面应用 / 跨平台打包与发布",
     r"tauri|electron|菜单栏|菜单条|悬浮窗|小组件|\bwidget\b|桌面|签名|打包",
     "desktop app packaging cross platform",
     "桌面封装与发布签名类 Skill 权重上调"),
    ("pwa-offline", "PWA / 离线能力与本地存储",
     r"\bpwa\b|service worker|离线|indexeddb|localstorage|local[- ]first|本地优先|不上传",
     "pwa offline indexeddb",
     "PWA 与离线 / 本地存储类 Skill 权重上调"),
    ("responsive", "响应式 Web（桌面 + 手机同一套）",
     r"响应式|移动优先|mobile[- ]first|自适应|手机屏|小屏",
     "responsive web design",
     "响应式布局类 Skill 权重上调"),
    ("supabase-db", "Supabase / Postgres / Migration 治理",
     r"supabase|postgres|plpgsql|数据库迁移|migration 治理|\brls\b|数据库",
     "supabase postgres migration rls",
     "数据库治理类 Skill 权重上调"),
    ("deploy", "部署上线（Vercel / 静态托管 / 云端）",
     r"vercel|netlify|cloudflare pages|部署|deploy|上线|发布链接",
     "vercel deployment static hosting",
     "部署发布类 Skill 权重上调"),
    ("llm-api", "LLM API 接入 / 流式与结构化输出",
     r"deepseek|openai|claude|qwen|百炼|dashscope|kimi|coze|大模型|\bllm\b|流式|结构化输出",
     "llm api streaming structured output",
     "LLM 接入与提示词类 Skill 权重上调"),
    ("secret-safety", "API Key / Secret 安全与配置收敛",
     r"byok|\bapi key\b|密钥|secret|凭证|不暴露|不外露",
     "secret management api key safety",
     "密钥 / Secret 安全类 Skill 权重上调"),
    ("github-auto", "GitHub 仓库自动化与内容同步",
     r"github actions|\bgh (cli|api)\b|ci/cd|自动采集|定时任务|自动更新|仓库治理",
     "github automation actions workflow",
     "GitHub 自动化类 Skill 权重上调"),
    ("agent-governance", "Agent / 多智能体治理与提示词工程",
     r"agent|智能体|多智能体|orca|提示词|编排|skill 治理|治理规则",
     "agent orchestration prompt engineering",
     "Agent 编排 / 提示词治理类 Skill 权重上调"),
    ("spec-driven", "SDD / SPEC / PLAN / TASK 开发流程",
     r"\bsdd\b|\bspec\b|需求文档|验收标准|开发流程|\bplan\b|拆解|路线图",
     "spec driven development plan task",
     "规格驱动开发流程类 Skill 权重上调"),
    ("python-auto", "Python 本地自动化 / 数据处理",
     r"\bpython\d?\b|openpyxl|excel 处理|\b脚本\b|批处理|自动化脚本|数据处理",
     "python automation scripting",
     "Python 本地自动化类 Skill 权重上调"),
    ("dashboard-viz", "数据看板 / 可视化与统计口径",
     r"看板|dashboard|可视化|图表|仪表盘|分位|统计口径|指标",
     "dashboard data visualization",
     "看板与可视化类 Skill 权重上调"),
    ("finance-calc", "金融 / 投资口径与计算",
     r"股息|估值|指数|回撤|基金|\betf\b|股票|a ?股|汇率|保险|盈亏|套利|行情",
     "investment dashboard finance analysis",
     "金融投研类 Skill 权重上调"),
    ("media-transcribe", "视频 / 音频转写与内容归档",
     r"whisper|转写|字幕|视频|音频|ffmpeg|obsidian|笔记",
     "whisper transcription knowledge base",
     "音视频转写与归档类 Skill 权重上调"),
    ("photo-mgmt", "图片素材管理 / EXIF 与相册",
     r"摄影|照片|图片|\bexif\b|素材|相册|机位|缩略图",
     "photo library exif management",
     "图片素材管理类 Skill 权重上调"),
    ("task-integration", "时间 / 任务管理工具集成",
     r"滴答|dida365|ticktick|日历|\btodo\b|习惯|打卡|复盘",
     "task management calendar integration",
     "任务 / 日历集成类 Skill 权重上调"),
    ("data-pipeline", "抓取 / RSS / 信息聚合流水线",
     r"\brss\b|rsshub|freshrss|抓取|爬虫|聚合|采集器",
     "rss aggregation data pipeline",
     "抓取与信息聚合类 Skill 权重上调"),
    ("docker-infra", "Docker / 自托管服务运维",
     r"docker|compose|自托管|self[- ]host|nginx|容器",
     "docker self hosted infrastructure",
     "容器化与自托管运维类 Skill 权重上调"),
    ("voice-input", "语音输入 / 语音识别",
     r"语音|听写|dictation|\bspeech\b|语音识别|输入法",
     "voice input speech recognition",
     "语音输入类 Skill 权重上调"),
    ("privacy-local", "本地优先 / 隐私与脱敏",
     r"隐私|脱敏|不上云|仅存浏览器|本地存储|加密|匿名",
     "privacy local data compliance",
     "隐私与脱敏类 Skill 权重上调"),
]

# 已知的「重量级技术方向」：当前完全没命中时，明确写进「低优先级」，避免日报乱推。
# 一旦真实命中，会自动进入对应条目而不是继续待在低优先级列表。
LOW_PRIORITY_CANDIDATES = [
    ("kubernetes", "Kubernetes / 集群编排", r"kubernetes|\bk8s\b|helm"),
    ("azure", "Azure", r"\bazure\b"),
    ("aws", "AWS（Lambda / S3）", r"\baws\b|amazon web services|\blambda\b|\bs3\b"),
    ("gcp", "GCP / Firebase", r"\bgcp\b|google cloud|firebase"),
    ("django", "Django / DRF", r"django"),
    ("flutter", "Flutter / Dart", r"flutter|\bdart\b"),
    ("unity", "Unity / 游戏引擎", r"unity|unreal"),
    ("web3", "Web3 / 智能合约", r"web3|solidity|智能合约"),
    ("kafka", "Kafka / 消息队列", r"kafka|rabbitmq|消息队列"),
    ("terraform", "Terraform / IaC", r"terraform|pulumi|ansible"),
]

STATE_RE = re.compile(r"<!--\s*SKILL_CONTEXT_STATE(.*?)-->", re.S)

# 生成时间戳不参与「内容是否变化」的判断：否则每天跑一次都会产生一次无意义 commit。
# 只归一化头部的生成/更新时间与状态块里的 generated 字段，不动项目本身的日期数据。
STAMP_RE = re.compile(
    r"((?:生成|更新)时间：)\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?"
    r"|(\"generated\"\s*:\s*)\"[^\"]*\""
)


def strip_timestamps(text):
    """抹掉生成时间戳，仅用于内容比对（不用于写出）。"""
    return STAMP_RE.sub(lambda m: m.group(1) or m.group(2) or "", text or "")


def read_text(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def write_if_changed(path, text, skip_if_unchanged=True):
    """写文件；skip_if_unchanged=True 且内容（忽略生成时间戳）没变时跳过写入。

    返回 True 表示确实写入了新内容，False 表示内容无实质变化。
    这样「无变化不制造空 commit」不依赖 git 也能成立，且跨平台一致。
    """
    if skip_if_unchanged:
        old = read_text(path)
        if old is not None and strip_timestamps(old) == strip_timestamps(text):
            return False
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True



# ------------------------------------------------------------------ 基础工具
# 代码块里出现的 bash / npm / docker 命令不是技术栈信号，先整块剔除。
CODE_FENCE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]{1,80}`", re.S)
HEADING = re.compile(r"^#{1,6}\s*(.+)$", re.M)


def strip_code(text):
    return CODE_FENCE.sub(" ", text or "")


def signal_parts(repo, desc_override):
    """拆成两段文本，用于「命中强度」判定：

    - head：仓库名 + 描述 + 主语言 + README 标题行 + README 声明的功能/技术栈段。
      出现在这里 = 项目自己声明了，命中 1 次即算。
    - body：去代码块后的 README 正文。这里的提及可能是顺口一提
      （比如治理文档里写「真机 adb/Expo 直驱」），需要出现 ≥2 次才算。
    """
    name = repo.get("name") or ""
    desc = (desc_override or {}).get(name) or repo.get("description") or ""
    readme = repo.get("readme") or ""
    declared = (repo.get("signal_tech") or []) + (repo.get("signal_feats") or [])
    heads = HEADING.findall(strip_code(readme))
    head = " ".join([name, desc, repo.get("language") or "", " ".join(heads),
                     " ".join(declared)])
    return head.lower(), strip_code(readme).lower()


def match_rule(pat, head, body, body_min):
    """规则命中判定：头部声明命中即算；仅正文命中时需达到最小出现次数。"""
    if re.search(pat, head, re.I):
        return True
    if body_min <= 1:
        return re.search(pat, body, re.I) is not None
    return len(re.findall(pat, body, re.I)) >= body_min


def repo_tech_keys(repo, desc_override):
    """单仓库命中的技术栈 key 集合（含主语言提示）。"""
    head, body = signal_parts(repo, desc_override)
    keys = {k for k, _l, _c, p in TECH if match_rule(p, head, body, BODY_MIN_TECH)}
    hint = LANG_HINTS.get(repo.get("language") or "")
    if hint:
        keys.add(hint)
    return keys


def _days(repo, today):
    stamp = (repo.get("updatedAt") or "")[:10]
    try:
        return (today - date.fromisoformat(stamp)).days
    except ValueError:
        return 9999


def _weight(days):
    if days <= HOT_DAYS:
        return W_HOT
    if days <= ACTIVE_DAYS:
        return W_ACTIVE
    if days <= WARM_DAYS:
        return W_WARM
    return W_STALE


def _fmt1(x):
    return ("%.1f" % x).rstrip("0").rstrip(".")


def _cut(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _tech_board(repos, today, desc_override):
    board = {}
    for repo in repos:
        keys = repo_tech_keys(repo, desc_override)
        days = _days(repo, today)
        w = _weight(days)
        for key in keys:
            _kk, label, category, _p = TECH_BY_KEY[key]
            item = board.setdefault(key, {
                "key": key, "label": label, "category": category,
                "weight": 0.0, "hot": 0, "active": 0, "total": 0,
            })
            item["weight"] += w
            item["total"] += 1
            if days <= HOT_DAYS:
                item["hot"] += 1
            if days <= ACTIVE_DAYS:
                item["active"] += 1
    return board


def _need_board(repos, today, desc_override):
    board = {}
    for repo in repos:
        head, body = signal_parts(repo, desc_override)
        days = _days(repo, today)
        w = _weight(days)
        for key, label, pat, kw, impact in NEEDS:
            if not match_rule(pat, head, body, BODY_MIN_NEED):
                continue
            item = board.setdefault(key, {
                "key": key, "label": label, "weight": 0.0,
                "hot": 0, "active": 0, "total": 0,
                "keywords": kw, "impact": impact,
            })
            item["weight"] += w
            item["total"] += 1
            if days <= HOT_DAYS:
                item["hot"] += 1
            if days <= ACTIVE_DAYS:
                item["active"] += 1
    return board


def _rank(board):
    return sorted(board.values(),
                  key=lambda i: (-i["weight"], -i["hot"], -i["active"], i["key"]))


def _parse_state(prev_text):
    if not prev_text:
        return None
    m = STATE_RE.search(prev_text)
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return None


# ------------------------------------------------------------------ 主渲染
def build_skill_context(repos, desc_override=None, today=None, prev_text=None,
                        updated_at=None, purpose_note=None):
    """生成 SKILL_CONTEXT.md 全文。

    repos: generate_portfolio.py 采集的仓库列表（同一次采集，不额外请求 API）。
    prev_text: 上一次生成的 SKILL_CONTEXT.md 全文，用于算「最近变化」；没有就写首次生成。
    """
    desc_override = desc_override or {}
    today = today or date.today()
    updated_at = updated_at or today.isoformat()

    tech = _tech_board(repos, today, desc_override)
    need = _need_board(repos, today, desc_override)

    total = len(repos)
    pub = sum(1 for r in repos if (r.get("visibility") or "").lower() == "public")
    pri = total - pub
    active30 = [r for r in repos if _days(r, today) <= ACTIVE_DAYS]
    hot14 = [r for r in repos if _days(r, today) <= HOT_DAYS]

    md = []
    md.append("# Skill 推荐背景\n")
    md.append("> 自动生成，请勿手工编辑")
    md.append("> 更新时间：%s（仅在有实质变化时更新，未变化不产生新提交）" % updated_at)
    md.append("> 数据来源：GITHUB_PROJECTS.md / GitHub 项目档案")
    md.append("> 用途：Skill 情报日报、Skill 推荐与排行个性化、Skill 搜索关键词生成")
    md.append("> 说明：本文件由确定性规则从项目档案派生，不调用任何大模型；两份文件来自同一次采集，无需重复请求 GitHub API。")
    md.append("> 注意：本文件属 Public 展示层，只含公开仓库；私有项目明细在内部注册表，不在此输出。\n")

    # 1 ----------------------------------------------------------------
    md.append("## 1. 当前项目概况\n")
    md.append("- 仓库总数：%d（公开 %d / 私有 %d）" % (total, pub, pri))
    md.append("- 最近 30 天活跃项目：%d 个（其中 14 天内活跃 %d 个）" % (len(active30), len(hot14)))
    if total:
        md.append("- 活跃度占比：%.0f%% 的仓库在 30 天内有提交" % (100.0 * len(active30) / total))
    md.append("- 当前主要开发类型：")
    for label, keys in DEV_TYPES:
        hit = [r for r in repos if repo_tech_keys(r, desc_override) & set(keys)]
        if not hit:
            continue
        h = sum(1 for r in hit if _days(r, today) <= ACTIVE_DAYS)
        md.append("  - %s — %d 个仓（30 天内活跃 %d）" % (label, len(hit), h))
    md.append("")

    # 2 ----------------------------------------------------------------
    md.append("## 2. 当前活跃项目\n")
    md.append("> 只列 14 天内活跃的仓库；技术栈取命中标签前 3 个。完整功能说明见 `GITHUB_PROJECTS.md`。\n")
    hot_sorted = sorted(hot14, key=lambda r: (_days(r, today), r.get("name") or ""))
    listed = hot_sorted[:HOT_LIST_MAX]
    for r in listed:
        keys = repo_tech_keys(r, desc_override)
        tags = [t[1] for t in TECH if t[0] in keys][:3]
        desc = (desc_override.get(r.get("name")) or r.get("description") or "(无描述)")
        md.append("- `%s` — %s — %s — %s" % (
            r.get("name"), _cut(desc, 46), " / ".join(tags) or "—",
            (r.get("updatedAt") or "")[:10]))
    if len(hot_sorted) > len(listed):
        md.append("- …另有 %d 个 14 天内活跃仓库未逐一列出，需要时读 `GITHUB_PROJECTS.md`。"
                  % (len(hot_sorted) - len(listed)))
    warm = len(active30) - len(hot14)
    if warm > 0:
        md.append("- 此外有 %d 个仓库在 15–30 天内活跃（正常权重，未列出）。" % warm)
    md.append("")

    # 3 ----------------------------------------------------------------
    md.append("## 3. 高频技术栈\n")
    md.append("> 权重 = 按仓库活跃度加权（14 天内 ×3 / 30 天内 ×2 / 90 天内 ×1 / 更早 ×0.3）。\n")
    tech_rank = _rank(tech)
    top_w = tech_rank[0]["weight"] if tech_rank else 0.0
    general = [t for t in tech_rank if t["category"] == "通用"]
    special = [t for t in tech_rank if t["category"] != "通用"]
    md.append("### 高频")
    for t in [x for x in general if top_w and x["weight"] >= top_w * 0.45]:
        md.append("- %s — 活跃 %d / 权重 %s" % (t["label"], t["active"], _fmt1(t["weight"])))
    if not any(top_w and x["weight"] >= top_w * 0.45 for x in general):
        md.append("- （暂无）")
    md.append("\n### 中高频")
    for t in [x for x in general if top_w and top_w * 0.18 <= x["weight"] < top_w * 0.45]:
        md.append("- %s — 活跃 %d / 权重 %s" % (t["label"], t["active"], _fmt1(t["weight"])))
    if not any(top_w and top_w * 0.18 <= x["weight"] < top_w * 0.45 for x in general):
        md.append("- （暂无）")
    md.append("\n### 专项")
    for t in special:
        md.append("- %s — 活跃 %d / 权重 %s" % (t["label"], t["active"], _fmt1(t["weight"])))
    for t in [x for x in general if not top_w or x["weight"] < top_w * 0.18]:
        md.append("- %s — 活跃 %d / 权重 %s（低频）" % (t["label"], t["active"], _fmt1(t["weight"])))
    if not special and not [x for x in general if not top_w or x["weight"] < top_w * 0.18]:
        md.append("- （暂无）")
    md.append("")

    # 4 ----------------------------------------------------------------
    md.append("## 4. 高频开发需求\n")
    md.append("> 从项目里抽象出的「能力需求」，是 Skill 推荐的主要依据。\n")
    need_rank = _rank(need)
    for n in need_rank:
        md.append("- %s — 活跃 %d / 权重 %s" % (n["label"], n["active"], _fmt1(n["weight"])))
    md.append("")

    # 5 ----------------------------------------------------------------
    md.append("## 5. Skill 推荐优先级\n")
    md.append("> 由得分实时计算，不是固定名单：P0 = 权重 ≥ 最高分 %d%% 且 14 天内活跃项目 ≥ %d 个；"
              "P1 = 权重 ≥ %d%%；更低为 P2。安装量高但当前项目用不上的 Skill 不进 P0。\n"
              % (int(P0_RATIO * 100), P0_MIN_HOT, int(P1_RATIO * 100)))
    top_need = need_rank[0]["weight"] if need_rank else 0.0
    p0, p1, p2 = [], [], []
    for n in need_rank:
        ratio = (n["weight"] / top_need) if top_need else 0.0
        if ratio >= P0_RATIO and n["hot"] >= P0_MIN_HOT:
            p0.append(n)
        elif ratio >= P1_RATIO:
            p1.append(n)
        else:
            p2.append(n)
    p0 = p0[:P0_MAX]

    def dump(title, items):
        md.append("### %s" % title)
        if not items:
            md.append("- （当前无）")
        for n in items:
            md.append("- %s — 活跃 %d（14 天内 %d）/ 权重 %s"
                      % (n["label"], n["active"], n["hot"], _fmt1(n["weight"])))
            md.append("  - 影响：%s" % n["impact"])
        md.append("")

    dump("P0 — 高优先级（多个活跃项目共用，或能明显减少重复踩坑）", p0)
    dump("P1 — 中优先级（已有真实场景，但不是所有项目都用）", p1)
    dump("P2 — 按需（只对应少数专项项目）", p2)

    # 低优先级：当前完全没命中的重量级方向，动态判定
    low_hits, low_absent = [], []
    for key, label, pat in LOW_PRIORITY_CANDIDATES:
        hit = [r for r in repos
               if match_rule(pat, *signal_parts(r, desc_override), BODY_MIN_NEED)]
        if hit:
            low_hits.append((label, len(hit)))
        else:
            low_absent.append(label)
    md.append("### 当前低优先级")
    if low_absent:
        md.append("- 项目里完全没有涉及，不进入推荐方向：%s" % "、".join(low_absent))
    else:
        md.append("- 无（已知重量级方向均有项目命中）")
    if low_hits:
        md.append("- 已出现但仅个别仓库命中，按需观察：%s"
                  % "、".join("%s（%d 个仓）" % (l, c) for l, c in low_hits))
    md.append("")

    # 6 ----------------------------------------------------------------
    md.append("## 6. Skill 搜索关键词\n")
    md.append("> 供日报智能体/搜索工具直接使用，按需求权重从高到低（P0 → P1 → P2）。\n")
    kws = []
    for n in p0 + p1 + p2:
        if n["keywords"] not in kws:
            kws.append(n["keywords"])
    for k in kws[:18]:
        md.append("- %s" % k)
    md.append("")

    # 7 ----------------------------------------------------------------
    md.append("## 7. 最近变化\n")
    md.append("> 只记录可能影响 Skill 推荐方向的变化；普通提交不入此表。\n")
    state = _parse_state(prev_text)
    cur_state = {
        "v": 1,
        "generated": updated_at,
        "totals": {"repos": total, "active30": len(active30), "hot14": len(hot14)},
        "needs": {n["key"]: {"w": round(n["weight"], 2), "hot": n["hot"], "active": n["active"]}
                  for n in need_rank},
        "tech": {t["key"]: {"w": round(t["weight"], 2), "active": t["active"]}
                 for t in tech_rank},
    }
    if not state:
        md.append("- 首次生成，暂无历史基线；从下一次运行起开始记录权重与活跃度变化。")
    else:
        old_needs = state.get("needs") or {}
        deltas = []
        for n in need_rank:
            o = old_needs.get(n["key"])
            if not o:
                deltas.append((n["weight"], n["label"], "新增", 0.0, n["weight"], n))
                continue
            d = n["weight"] - float(o.get("w", 0))
            if abs(d) >= REL_CHANGE:
                deltas.append((abs(d), n["label"], "上升" if d > 0 else "下降",
                               float(o.get("w", 0)), n["weight"], n))
        gone = [v for k, v in old_needs.items()
                if k not in cur_state["needs"] and float(v.get("w", 0)) >= REL_CHANGE]
        deltas.sort(key=lambda x: -x[0])
        if deltas or gone:
            for _a, label, direction, w0, w1, n in deltas[:8]:
                md.append("- %s `%s` 权重 %s → %s（活跃 %d / 14 天内 %d）→ %s"
                          % (direction, label, _fmt1(w0), _fmt1(w1), n["active"], n["hot"],
                             n.get("impact") or "关注权重变化"))
            if gone:
                md.append("- 退出评分：%s（本次采集未再命中）" % "、".join(
                    "`%s`" % k for k in gone[:6]))
        else:
            md.append("- 无影响推荐方向的变化（各需求权重波动均 < %s）。" % _fmt1(REL_CHANGE))
        old_t = state.get("totals") or {}
        if old_t:
            md.append("- 规模变化：仓库 %s → %d，30 天内活跃 %s → %d，14 天内活跃 %s → %d"
                      % (old_t.get("repos", "?"), total, old_t.get("active30", "?"),
                         len(active30), old_t.get("hot14", "?"), len(hot14)))
    md.append("")

    md.append("---\n")
    md.append("## 机器可读状态\n")
    md.append("> 供下一次生成时对比「最近变化」，勿删。\n")
    md.append("<!-- SKILL_CONTEXT_STATE\n%s\n-->"
              % json.dumps(cur_state, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    return "\n".join(md) + "\n"
