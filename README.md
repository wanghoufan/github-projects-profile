# GitHub 项目全景档案（给智能体的背景材料）

一份结构化 Markdown，供 AI 智能体快速了解账号 `wanghoufan` 正在开发的项目、技术栈与最新进度，从而给出更针对性的建议，而不是泛泛而谈。

- 生成时间：**2026-09-22** ｜ 仓库总数：**41**（公开 21 / 私有 20）｜ 主题分组：**13**
- 主文件：[`GITHUB_PROJECTS.md`](./GITHUB_PROJECTS.md)

## 智能体怎么用

直接读主文件即可，推荐原始直链：

```
https://raw.githubusercontent.com/<owner>/<repo>/main/GITHUB_PROJECTS.md
```

建议读取顺序：先看顶部「总览」表定位相关项目 → 再跳到对应主题分组看「功能 / 技术栈 / 最新进度」→ 需要细看时走仓库链接。

## 每个项目包含哪些字段

| 字段 | 说明 |
|---|---|
| 定位 | 一句话说明这个项目是干什么的 |
| 链接 / 预览 / 语言 / 更新时间 / Stars | 基本元信息 |
| 功能 | 从 README 功能段提炼 |
| 技术栈 | 从 README 技术栈段提炼，缺失时回退主语言 |
| 最新进度 | 更新时间 + README 状态行，或最近一次 commit |

公开 / 私有分别标注；≥30 天未提交的仓库会标 `⚠️ 长期停滞`。

## 怎么更新

用 `scripts/generate_portfolio.py` 重新采集（依赖本机 `gh` 已登录且 token 含 `repo` 权限，否则看不到私有仓库）：

```bash
python3 scripts/generate_portfolio.py
```

默认输出到用户级目录 `~/.workbuddy/GITHUB_PROJECTS.md`，也可用环境变量改：

```bash
PORTFOLIO_OUT=/abs/path/out.md python3 scripts/generate_portfolio.py   # 改输出路径
PORTFOLIO_USER=otherlogin python3 scripts/generate_portfolio.py         # 改目标账号
```

跑一遍约 2 分钟（41 个仓库 × 逐仓请求 README 与最近提交，串行），后台跑即可。

## 已知偏差

- README 缺失的仓库只有仓库名 + 最近提交，描述需人工补（写进脚本里的 `DESCRIPTION_OVERRIDE`）。
- 段落提取是启发式的（按标题抓功能 / 技术栈段），个别项目可能偏简。
- `GROUPS` 与 `DESCRIPTION_OVERRIDE` 里的仓库名是「迁移时替换」的配置项，换账号时替换成目标账号的实际仓库名即可。

## 声明

本档案由仓库所有者本人主动公开，内容包含私有仓库的名称、功能描述、技术栈与近期进度。仅用于让智能体了解项目背景，不代表开源授权。
