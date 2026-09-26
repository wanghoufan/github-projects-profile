# GitHub 项目全景档案（给智能体的背景材料）

两份 Markdown，都由 `scripts/generate_portfolio.py` 从**同一次** GitHub 采集结果自动生成，供 AI 智能体按需读取。

| 文件 | 定位 | 什么时候读 |
|---|---|---|
| [`PROJECT_MAP.md`](./PROJECT_MAP.md) | **项目身份与编号 SSOT**：本地目录 ↔ Project ID ↔ GitHub 仓库 | 需要知道某个编号对应哪个仓库、或某仓库对应哪个本地目录 |
| [`GITHUB_PROJECTS.md`](./GITHUB_PROJECTS.md) | 完整 GitHub 项目档案 | 需要深入理解单个项目、具体技术实现、最新进度 |
| [`SKILL_CONTEXT.md`](./SKILL_CONTEXT.md) | Skill Intelligence 的轻量需求画像 | Skill 日报、Skill 推荐、排行个性化、搜索关键词生成、判断某项 Skill 对当前项目群的适配度 |

## 项目编号与映射（SSOT）

本仓是**目录**，不是第二份源码仓库：这里只记录编号、名称、映射与状态，不记录代码副本、密钥或 `.env` 内容。

命名契约：

- **Project ID** `PNNN` 与本地目录三位编号永久一致，`ing`→`done` 不改变编号。
- **本地目录** `NNN-状态-中文名`，面向人的可读性。
- **GitHub 仓库** `pNNN-english-slug`，面向互联网；不含 `ing`/`done`，不含版本号。
- 一个项目一个主仓库；Public / Private 只是可见性属性，**不为展示而复制第二份同内容仓库**。
- 真正独立发布的多平台仓库共用同一 Project ID + 角色后缀（`-mac` / `-windows`）。
- `000-*` 是基础设施目录，暂不纳入 P 编号，单独列在映射表下半区。

数据源是机器可读的 [`PROJECT_MAP.tsv`](./PROJECT_MAP.tsv)，Markdown 视图由脚本渲染，二者不要手工分别改：

```bash
python3 scripts/project_github_audit.py --fetch   # 只读对账：Git/origin/远端存在/dirty/ahead/behind/重复映射/孤儿
python3 scripts/render_project_map.py --audit /tmp/audit.json   # 由 TSV + 审计结果重渲 PROJECT_MAP.md
```

对账工具只检查、不改写（不 commit / push / rename / 改可见性）。退出码：`0` 全部干净，`1` 有需人工处理的问题，`2` 扫描或环境失败。

## 新项目怎么出生（Project Steward）

上面的命名契约由 Project Bootstrapper 落地。**以后新项目不要手工建**。

本仓库是 **Public 展示层**，只放脱敏后的公开档案。执行器源码、完整注册表 `PROJECT_MAP.tsv`、编号台账 `PROJECT_RESERVATIONS.tsv`、事务状态都在 **内部治理层**：`../000-alw-steward 内部治理/`（不公开，也不进本仓历史）。

```bash
python3 "../000-alw-steward 内部治理/steward/steward.py" --help   # 全部子命令
```

| 能力 | 命令 | 说明 |
|---|---|---|
| 临时试验 | `create-scratch` | 只落 `2.Scratch/` + 本地 Git，不占 P 编号、不建 GitHub、不写表 |
| 正式项目 | `create-project` | 取号 → 建目录 → Git → Private 仓库 → push → `.project.yaml` → 表 + 档案 |
| 晋升 | `promote-project` | Scratch → 正式，代码与 Git 历史整体搬迁，不重建 |
| 审计 | `audit-project` / `check-backup` / `sync-registry` / `next-id` | 只读三方核对（目录 ↔ `.project.yaml` ↔ 表 ↔ GitHub） |
| 生命周期 | `change-status` | `ing/paused/done/archived`，P 编号与仓库名不变；只提交自己改的那个元数据文件 |
| 编号治理 | `reserve` / `list-transactions` | 出现过 / 测试占用过的号永久保留（tombstone），编号只增不减 |
| 修复 | `repair-remote` | 把 origin 指回登记表里的仓库 |
| 安全 | `scan-secrets`（工作树 / 暂存 / Git 历史三层）/ `--dry-run` / `--resume <transaction_id>` | 首次 push 前拦密钥；事务半完成可续跑，不重复占号 |

隔离实例（`STEWARD_CODING` 指向别处）自动走 **mock GitHub 后端**，只建本地 bare 仓，物理上碰不到真实账号；只有生产工作区的命令才会访问 GitHub。

角色规则、意图分类和「什么时候必须停下来问用户」写在内部治理层的 `steward/PROJECT_STEWARD.md`。
用户侧只需要说「临时试一下 X」「正式创建 X」「把刚才那个转正式项目」。本仓库的公开清单只列 Public 仓库；私有项目的中文名、本地目录与治理说明不出现在这里。


**读取顺序**：日报类智能体默认只读 `SKILL_CONTEXT.md`；只有当需要判断某个 Skill 是否适配某个**具体项目**时，才再进 `GITHUB_PROJECTS.md`。不要让日报每天读完整档案（约 40KB），那是浪费。

直链（把 `<owner>/<repo>` 换成实际地址即可）：

```
https://raw.githubusercontent.com/<owner>/<repo>/main/SKILL_CONTEXT.md     # 日报默认读这个
https://raw.githubusercontent.com/<owner>/<repo>/main/GITHUB_PROJECTS.md   # 需要时再读
```

## SKILL_CONTEXT.md 里有什么

7 个固定板块，结构稳定、机器可读、篇幅远小于完整档案：

| 板块 | 回答的问题 |
|---|---|
| 1. 当前项目概况 | 仓库总数、近 30 天活跃数、当前主要在开发什么类型 |
| 2. 当前活跃项目 | 14 天内活跃的仓库：一句话定位 + 技术栈 + 最近更新 |
| 3. 高频技术栈 | 按活跃度加权排序（高频 / 中高频 / 专项） |
| 4. 高频开发需求 | 从项目抽象出的**能力需求**（不是技术名） |
| 5. Skill 推荐优先级 | P0 / P1 / P2 + 当前低优先级方向 |
| 6. Skill 搜索关键词 | 一组英文关键词，可直接拿去搜 Skill |
| 7. 最近变化 | 只记录会影响推荐方向的权重变化 |

几条硬规则：

- **不用大模型**：全部由确定性 Python 规则（`scripts/skill_context.py`）从项目档案派生，同一份输入必得同一份输出，跑一次成本几乎为零。
- **不重复请求 API**：与 `GITHUB_PROJECTS.md` 共用同一次采集结果。
- **优先级是算出来的，不是写死的**：得分 = Σ 仓库活跃度权重（14 天内 ×3 / 30 天内 ×2 / 90 天内 ×1 / 更早 ×0.3）；P0 还要求至少 2 个 14 天内活跃的仓库。搜索量大但当前项目用不上的 Skill 不会进 P0。
- **活跃度决定权重**：几个月没动的项目和昨天刚提交的项目不会被同等对待。
- **技术栈只认「项目自己声明的」**：仓库名 / 描述 / 主语言 / README 标题行 / README 的功能段与技术栈段命中 1 次即算；只在 README 正文里出现的词需要出现 ≥3 次才算，避免「顺口提一句」被当成技术栈。
- 「最近变化」靠文件末尾的机器可读状态块（`SKILL_CONTEXT_STATE`）与上一次生成结果对比得出；删掉那个块即等于重置基线。

## GITHUB_PROJECTS.md 里有什么

一份结构化 Markdown，供 AI 智能体快速了解账号正在开发的项目、技术栈与最新进度，从而给出更针对性的建议。

- 顶部「总览」表按最近更新排序，先定位相关项目；下方按 13 个主题分组详述。
- 每个项目的字段：

| 字段 | 说明 |
|---|---|
| 定位 | 一句话说明这个项目是干什么的 |
| 链接 / 预览 / 语言 / 更新时间 / Stars | 基本元信息 |
| 功能 | 从 README 功能段提炼 |
| 技术栈 | 从 README 技术栈段提炼，缺失时回退主语言 |
| 最新进度 | 更新时间 + README 状态行，或最近一次 commit |

公开 / 私有分别标注；≥30 天未提交的仓库会标 `⚠️ 长期停滞`。

## 怎么更新

依赖本机 `gh` 已登录且令牌含 `repo` 权限（否则看不到私有仓库）：

```bash
python3 scripts/generate_portfolio.py
```

默认输出到用户级目录 `~/.workbuddy/` 的**两份**文件，也可用环境变量覆盖：

```bash
PORTFOLIO_OUT=/abs/path/GITHUB_PROJECTS.md SKILL_CONTEXT_OUT=/abs/path/SKILL_CONTEXT.md \
  python3 scripts/generate_portfolio.py     # 指定输出位置（CI 里就是这么用的）
PORTFOLIO_USER=otherlogin python3 scripts/generate_portfolio.py   # 换目标账号
PORTFOLIO_DUMP_JSON=/tmp/raw.json python3 scripts/generate_portfolio.py  # 另存采集结果，供离线调试
PORTFOLIO_WRITE_ALWAYS=1 python3 scripts/generate_portfolio.py    # 即使内容没变也强制重写
```

跑一遍约 1.5 分钟（40+ 个仓库 × 逐仓请求 README 与最近提交，串行），后台跑即可。

运行日志里有一段「采集诊断」，会明确区分：正常空仓库 / 无 README、README 拉取失败、最近提交拉取失败、网络抖动重试次数。**退出码**：`0` 正常；`1` 有仓库内容没拉到（文件仍会写出，但状态标记为失败）；`2` 连仓库列表都没拿到（鉴权或网络问题）。

## 每日自动更新

`.github/workflows/daily-update.yml`：每天 **07:00（Asia/Shanghai）** 自动执行一次

```
采集 GitHub 项目数据 → 更新 GITHUB_PROJECTS.md → 更新 SKILL_CONTEXT.md → 有变化才提交
```

- 两份文件内容（忽略生成时间戳，即头部时间与状态块里的 generated 字段）都没有实质变化时，脚本不重写文件、工作流不提交，**不会产生空 commit**。
- 也支持手动触发：仓库 Actions 页面选这个 workflow → Run workflow。
- **需要在仓库 Secrets 里配置 `PORTFOLIO_TOKEN`**：一个带 `repo` 权限的 Personal Access Token（Settings → Secrets and variables → Actions → New repository secret）。没配的话会退回默认 `GITHUB_TOKEN`，而它只能看到本仓库，工作流会在「令牌权限自检」一步明确报错，不会静默生成残缺档案。

失败时按日志定位：

| 症状 | 位置 |
|---|---|
| 令牌失效 / 权限不足（401 / 403） | 「令牌权限自检」步骤，以及日志里的 `gh failed: … 401/403` |
| 私有仓库读不到 | 同上，检查令牌是否含 `repo` 权限 |
| 个别仓库 README / 提交拉取失败 | 「采集诊断」区会逐条列出仓库名与原因 |
| 文件生成失败 | 日志里的 `Traceback` |
| 提交 / 推送失败 | 「仅在有实质变化时提交」步骤；若分支被保护，需放开对 `github-actions[bot]` 的限制 |

## 已知偏差

- README 缺失的仓库只有仓库名 + 最近提交，描述需人工补（写进脚本里的 `DESCRIPTION_OVERRIDE`）。
- 段落提取是启发式的（按标题抓功能 / 技术栈段），个别项目可能偏简；技术栈识别也是关键词规则，遇到跨平台仓库（如 .NET + Avalonia 同时出 macOS 与 Windows 客户端）会同时计入两个平台标签。
- `GROUPS`、`DESCRIPTION_OVERRIDE`、`TECH`、`NEEDS` 里的仓库名与关键词是「迁移时替换 / 需要时增删」的配置项；换账号时替换成目标账号的实际内容即可。改规则前先读 `scripts/skill_context.py` 顶部的维护说明。

## 声明

本档案由仓库所有者本人主动公开，内容包含私有仓库的名称、功能描述、技术栈与近期进度。仅用于让智能体了解项目背景，不代表开源授权；请勿再对外分发。
