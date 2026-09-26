# 项目映射表（Project ID SSOT）

> 由 `scripts/render_project_map.py` 生成于 2026-09-26，数据源 `PROJECT_MAP.tsv`。
> 本仓是项目总目录，不是第二份源码仓库：这里只记录名称、编号、映射与状态，不记录代码副本、密钥或 `.env`。

## 编号规则

- Project ID `PNNN` 与本地目录三位编号永久一致，状态由 `ing` 变 `done` 时不变。
- 本地目录保留中文与状态：`NNN-状态-中文名`，面向人。
- GitHub 仓库统一 `pNNN-english-slug`，不含 ing/done，不含版本号，面向互联网。
- 一个项目只有一个主仓库；Public / Private 只是可见性属性，不为展示复制第二份代码。
- 真正独立发布的多平台仓库共用一个 Project ID，加角色后缀（如 `-mac` / `-windows`）。
- `000-*` 是基础设施目录，暂不纳入 P 编号。

## 一览表

| Project ID | 本地目录 | GitHub Repo | 可见性 | 生命周期 | Backup | 结论 |
|---|---|---|---|---|---|---|
| P001 | `001-ing-家庭保单数据看板` | `p001-family-insurance-dashboard` | PUBLIC | ing | PARTIAL | BEHIND_REMOTE, DUPLICATE_MAPPING; renamed |
| P002 | `002-ing-第三周作业-24-生活物种测试` | `p002-life-species-test` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P003 | `003-ing-个人网站项目-site` | `p003-houfan-xuezhang-site` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P004 | `004-done-gpt-cc-ds监控工具` | `DeepSeekBalanceWidget` | PUBLIC | done | PARTIAL | NAME_NOT_NUMBERED, DIRTY_WORKTREE, UNPUSHED_COMMITS, BEHIND_REMOTE; NOT_RENAMED 与 P010 同一产品线，需人工定 Project ID |
| P005 | `005-ing-家族图谱管理器` | `p005-qinyuan-tupu` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P006 | `006-ing-提示词管理器` | `p006-prompt-manager` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE, DUPLICATE_MAPPING; renamed |
| P007 | `007-ing-家族图谱管理器-模板-ORCA-副本` | `-` | - | ing | NONE | NO_ORIGIN; NO_ORIGIN 仓库零 commit |
| P008 | `008-ing-语音输入法` | `p008-no-more-typing` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE, BEHIND_REMOTE; renamed |
| P009 | `009-ing-滴答清单CLI` | `p009-dida365-time-system` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P010 | `010-ing-DS-GPT桌面额度显示工具` | `DeepSeekBalanceWidget-Mac` | PUBLIC | ing | COMPLETE | NAME_NOT_NUMBERED; NOT_RENAMED 与 P004 同一产品线，需人工定 Project ID |
| P011 | `011-ing-个人打卡小工具` | `p011-place-journal` | PUBLIC | ing | PARTIAL | BEHIND_REMOTE, DUPLICATE_MAPPING; renamed |
| P012 | `012-ing-个人投资组合平衡面板` | `-` | - | ing | NONE | NOT_GIT; NOT_GIT LOCAL_ONLY 无仓库 |
| P013 | `013-ing-滚仓计算器V2.0` | `p013-roll-position-calculator` | PUBLIC | ing | COMPLETE | OK; renamed git 在二级目录 |
| P014 | `014-ing-山寨滚仓网站` | `pepe-doge-breakout-radar-deepseek-v4-pro` | PUBLIC | ing | PARTIAL | NAME_NOT_NUMBERED, DIRTY_WORKTREE, BEHIND_REMOTE; NOT_RENAMED 同产品线存在 KIMI 变体仓 |
| P015 | `015-ing-photo-library` | `p015-photo-library` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P016 | `016-ing-懒得打字-安卓版本` | `p016-landedazi-android` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P017 | `017-ing-RSS聚合-个人信息雷达` | `p017-personal-rss` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P018 | `018-ing-本地视频转文字工具` | `p018-video2obsidian-mac` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed Windows 孪生仓本机无 checkout |
| P019 | `019-ing-摄影图库app` | `p019-photo-spot-app` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P020 | `020-ing-拉伸换边app` | `p020-stretch-side-timer` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed 另有未绑定旧仓 stretch-side-timer |
| P021 | `021-ing-workbuddy-switch` | `-` | - | ing | NONE | REMOTE_NOT_FOUND; WRONG_OWNER origin=changexbc/workbuddy-switch 未改动 |
| P022 | `022-ing-葫芦军师红利指数看板` | `p022-hongli-dixin-calc` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P023 | `023-ing-A股十一大指数-十年估值分位汇总` | `p023-a-share-index-valuation` | PUBLIC | ing | COMPLETE | OK; renamed git 在二级目录 |
| P024 | `024-ing-葫芦军师已下载清单整理` | `-` | - | ing | NONE | NOT_GIT; NOT_GIT LOCAL_ONLY 无仓库 |
| P025 | `025-ing-拉伸语音播报 app` | `p025-stretch-routine-app` | PUBLIC | ing | COMPLETE | OK; renamed |
| P026 | `026-ing-夜间补光灯` | `p026-yejian-buguangdeng` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P027 | `027-ing-蛋白质计算器` | `p027-protein-calculator` | PRIVATE | ing | COMPLETE | OK; renamed git 在二级目录 |
| P028 | `028-ing-酒吧聚会社交导演` | `p028-party-night` | PUBLIC | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P029 | `029-ing-图片本地整理项目` | `p029-photo-library-local` | PRIVATE | ing | PARTIAL | DIRTY_WORKTREE; renamed |
| P030 | `030-ing-skill 日报体系` | `p030-skill-daily` | PUBLIC | ing | COMPLETE | OK; renamed |

## 000-* 基础设施 / 嵌套 / 外部 / 未绑定仓库

| 类型 | 本地目录 | GitHub Repo | 可见性 | 结论 |
|---|---|---|---|---|
| nested | `002-ing-第三周作业-24-生活物种测试/ing 丨 0825 workbuddy探索/WorkBuddy教程` | `workbuddy-dual-axis-tutorial` | PRIVATE | OK; 嵌套仓 无独立编号 需人工定归属 |
| infra | `000-alw-github 档案` | `github-projects-profile` | PUBLIC | DIRTY_WORKTREE, UNPUSHED_COMMITS; 000-* 不纳入 P 编号 |
| infra | `000-alw-数据库管理专家` | `alw-db-governance` | PRIVATE | DIRTY_WORKTREE; 000-* 不纳入 P 编号 |
| infra | `000-alw-个人偏好-电脑治理仓库-skill管理` | `-` | - | NOT_GIT; NOT_GIT 000-* 待人工决定是否建 S 编号 |
| infra | `000-alw-自动化任务` | `-` | - | NOT_GIT; NOT_GIT 000-* 待人工决定是否建 S 编号 |
| external | `../docker/prompt-manager` | `p006-prompt-manager` | PRIVATE | DIRTY_WORKTREE, DUPLICATE_MAPPING; DUPLICATE_MAPPING 同 repo 的第二份本地 checkout |
| external | `../docker/family-insurance-dashboard` | `p001-family-insurance-dashboard` | PUBLIC | BEHIND_REMOTE, DUPLICATE_MAPPING; DUPLICATE_MAPPING 同 repo 的第二份本地 checkout |
| external | `../docker/personal-checkin` | `p011-place-journal` | PUBLIC | BEHIND_REMOTE, DUPLICATE_MAPPING; DUPLICATE_MAPPING 同 repo 的第二份本地 checkout |
| external | `../Infrastructure/orca-deepseek-bridge` | `orca-deepseek-bridge` | PRIVATE | OK; 1.Active 之外 有本地 checkout 非孤儿 |
| external | `../4.Templates（PC）/2026-09-09 丨 MAC 丨 ORCA V2.1 治理模板 丨 分发版-2026-09-11` | `orca-v2.1-governance` | PUBLIC | DIRTY_WORKTREE; 1.Active 之外 有本地 checkout 非孤儿 |
| orphan | `-` | `24-species-test` | PRIVATE | GITHUB_ORPHAN; 空仓库 建议人工确认后归档 |
| orphan | `-` | `50-haikou-cafes` | PUBLIC | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `DeepSeekBalanceWidget-Windows` | PUBLIC | GITHUB_ORPHAN; P004/P010 产品线孪生仓 本机无 checkout |
| orphan | `-` | `Video2Obsidian-Windows` | PRIVATE | GITHUB_ORPHAN; P018 产品线孪生仓 本机无 checkout |
| orphan | `-` | `ai-resume-job-matcher` | PUBLIC | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `ai-storyboard-generator` | PRIVATE | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `cny-rate-board` | PRIVATE | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `cny-us-rate-board` | PUBLIC | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `nomad-seasons` | PUBLIC | GITHUB_ORPHAN; GITHUB_ORPHAN |
| orphan | `-` | `orca-governance-validation-progress` | PRIVATE | GITHUB_ORPHAN; 归档仓 |
| orphan | `-` | `pepe-doge-breakout-radar-KIMI-K2.7-CODE` | PUBLIC | GITHUB_ORPHAN; P014 产品线变体仓 本机无 checkout |
| orphan | `-` | `personal-website` | PRIVATE | GITHUB_ORPHAN; 疑似 P003 旧版本 |
| orphan | `-` | `skills-manager-backup` | PRIVATE | GITHUB_ORPHAN; 000 基础设施备份仓 |
| orphan | `-` | `stretch-side-timer` | PUBLIC | GITHUB_ORPHAN; 疑似 P020 前代仓 需人工确认后归档 |

## 标准档案字段（逐项目）

```text
Project ID: P001
中文名: 家庭保单数据看板
本地目录: 001-ing-家庭保单数据看板
Git Root: 001-ing-家庭保单数据看板
GitHub Repo: wanghoufan/p001-family-insurance-dashboard
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: BEHIND_REMOTE, DUPLICATE_MAPPING
Dirty / Ahead / Behind: 0 / 0 / 1
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P002
中文名: 24 生活物种测试
本地目录: 002-ing-第三周作业-24-生活物种测试
Git Root: 002-ing-第三周作业-24-生活物种测试
GitHub Repo: wanghoufan/p002-life-species-test
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 1 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P003
中文名: 个人网站 site
本地目录: 003-ing-个人网站项目-site
Git Root: 003-ing-个人网站项目-site
GitHub Repo: wanghoufan/p003-houfan-xuezhang-site
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 4 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P004
中文名: DeepSeek/CC/DS 监控
本地目录: 004-done-gpt-cc-ds监控工具
Git Root: 004-done-gpt-cc-ds监控工具
GitHub Repo: wanghoufan/DeepSeekBalanceWidget
Visibility: PUBLIC
Lifecycle: done
Repo Role: main
Backup Status: NAME_NOT_NUMBERED, DIRTY_WORKTREE, UNPUSHED_COMMITS, BEHIND_REMOTE
Dirty / Ahead / Behind: 4 / 7 / 25
Last Verified: 2026-09-26
Note: NOT_RENAMED 与 P010 同一产品线，需人工定 Project ID
```

```text
Project ID: P005
中文名: 家族图谱管理器
本地目录: 005-ing-家族图谱管理器
Git Root: 005-ing-家族图谱管理器
GitHub Repo: wanghoufan/p005-qinyuan-tupu
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 17 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P006
中文名: 提示词管理器
本地目录: 006-ing-提示词管理器
Git Root: 006-ing-提示词管理器
GitHub Repo: wanghoufan/p006-prompt-manager
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE, DUPLICATE_MAPPING
Dirty / Ahead / Behind: 2 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P007
中文名: 家族图谱 ORCA 模板副本
本地目录: 007-ing-家族图谱管理器-模板-ORCA-副本
Git Root: 007-ing-家族图谱管理器-模板-ORCA-副本
GitHub Repo: wanghoufan/-
Visibility: -
Lifecycle: ing
Repo Role: main
Backup Status: NO_ORIGIN
Dirty / Ahead / Behind: - / - / -
Last Verified: 2026-09-26
Note: NO_ORIGIN 仓库零 commit
```

```text
Project ID: P008
中文名: 懒得打字 macOS
本地目录: 008-ing-语音输入法
Git Root: 008-ing-语音输入法
GitHub Repo: wanghoufan/p008-no-more-typing
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE, BEHIND_REMOTE
Dirty / Ahead / Behind: 5 / 0 / 20
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P009
中文名: 滴答清单时间体系
本地目录: 009-ing-滴答清单CLI
Git Root: 009-ing-滴答清单CLI
GitHub Repo: wanghoufan/p009-dida365-time-system
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 16 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P010
中文名: DS/GPT 桌面额度 Mac
本地目录: 010-ing-DS-GPT桌面额度显示工具
Git Root: 010-ing-DS-GPT桌面额度显示工具
GitHub Repo: wanghoufan/DeepSeekBalanceWidget-Mac
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: NAME_NOT_NUMBERED
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: NOT_RENAMED 与 P004 同一产品线，需人工定 Project ID
```

```text
Project ID: P011
中文名: 个人打卡小工具
本地目录: 011-ing-个人打卡小工具
Git Root: 011-ing-个人打卡小工具
GitHub Repo: wanghoufan/p011-place-journal
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: BEHIND_REMOTE, DUPLICATE_MAPPING
Dirty / Ahead / Behind: 0 / 0 / 24
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P012
中文名: 个人投资组合平衡面板
本地目录: 012-ing-个人投资组合平衡面板
Git Root: 012-ing-个人投资组合平衡面板
GitHub Repo: wanghoufan/-
Visibility: -
Lifecycle: ing
Repo Role: main
Backup Status: NOT_GIT
Dirty / Ahead / Behind: - / - / -
Last Verified: 2026-09-26
Note: NOT_GIT LOCAL_ONLY 无仓库
```

```text
Project ID: P013
中文名: 滚仓计算器 V2.0
本地目录: 013-ing-滚仓计算器V2.0
Git Root: 013-ing-滚仓计算器V2.0/excel-html-1-2-25-20
GitHub Repo: wanghoufan/p013-roll-position-calculator
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: OK
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: renamed git 在二级目录
```

```text
Project ID: P014
中文名: 山寨滚仓雷达 deepseek
本地目录: 014-ing-山寨滚仓网站
Git Root: 014-ing-山寨滚仓网站/pepe-doge-breakout-radar-deepseek-v4-pro
GitHub Repo: wanghoufan/pepe-doge-breakout-radar-deepseek-v4-pro
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: NAME_NOT_NUMBERED, DIRTY_WORKTREE, BEHIND_REMOTE
Dirty / Ahead / Behind: 253 / 0 / 16
Last Verified: 2026-09-26
Note: NOT_RENAMED 同产品线存在 KIMI 变体仓
```

```text
Project ID: P015
中文名: 摄影图库 PWA
本地目录: 015-ing-photo-library
Git Root: 015-ing-photo-library
GitHub Repo: wanghoufan/p015-photo-library
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 37 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P016
中文名: 懒得打字 安卓版
本地目录: 016-ing-懒得打字-安卓版本
Git Root: 016-ing-懒得打字-安卓版本
GitHub Repo: wanghoufan/p016-landedazi-android
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 66 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P017
中文名: RSS 聚合信息雷达
本地目录: 017-ing-RSS聚合-个人信息雷达
Git Root: 017-ing-RSS聚合-个人信息雷达
GitHub Repo: wanghoufan/p017-personal-rss
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 17 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P018
中文名: 视频转 Obsidian Mac
本地目录: 018-ing-本地视频转文字工具
Git Root: 018-ing-本地视频转文字工具
GitHub Repo: wanghoufan/p018-video2obsidian-mac
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 4 / 0 / 0
Last Verified: 2026-09-26
Note: renamed Windows 孪生仓本机无 checkout
```

```text
Project ID: P019
中文名: 摄影约拍机位库
本地目录: 019-ing-摄影图库app
Git Root: 019-ing-摄影图库app
GitHub Repo: wanghoufan/p019-photo-spot-app
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 46 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P020
中文名: 拉伸换边计时 App
本地目录: 020-ing-拉伸换边app
Git Root: 020-ing-拉伸换边app
GitHub Repo: wanghoufan/p020-stretch-side-timer
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 26 / 0 / 0
Last Verified: 2026-09-26
Note: renamed 另有未绑定旧仓 stretch-side-timer
```

```text
Project ID: P021
中文名: workbuddy switch
本地目录: 021-ing-workbuddy-switch
Git Root: 021-ing-workbuddy-switch
GitHub Repo: wanghoufan/-
Visibility: -
Lifecycle: ing
Repo Role: main
Backup Status: REMOTE_NOT_FOUND
Dirty / Ahead / Behind: - / - / -
Last Verified: 2026-09-26
Note: WRONG_OWNER origin=changexbc/workbuddy-switch 未改动
```

```text
Project ID: P022
中文名: 红利指数看板
本地目录: 022-ing-葫芦军师红利指数看板
Git Root: 022-ing-葫芦军师红利指数看板
GitHub Repo: wanghoufan/p022-hongli-dixin-calc
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 3 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P023
中文名: A股指数估值分位
本地目录: 023-ing-A股十一大指数-十年估值分位汇总
Git Root: 023-ing-A股十一大指数-十年估值分位汇总/a-share-index-valuation-report
GitHub Repo: wanghoufan/p023-a-share-index-valuation
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: OK
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: renamed git 在二级目录
```

```text
Project ID: P024
中文名: 葫芦军师清单整理
本地目录: 024-ing-葫芦军师已下载清单整理
Git Root: 024-ing-葫芦军师已下载清单整理
GitHub Repo: wanghoufan/-
Visibility: -
Lifecycle: ing
Repo Role: main
Backup Status: NOT_GIT
Dirty / Ahead / Behind: - / - / -
Last Verified: 2026-09-26
Note: NOT_GIT LOCAL_ONLY 无仓库
```

```text
Project ID: P025
中文名: 拉伸语音播报 App
本地目录: 025-ing-拉伸语音播报 app
Git Root: 025-ing-拉伸语音播报 app
GitHub Repo: wanghoufan/p025-stretch-routine-app
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: OK
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P026
中文名: 夜间补光灯
本地目录: 026-ing-夜间补光灯
Git Root: 026-ing-夜间补光灯
GitHub Repo: wanghoufan/p026-yejian-buguangdeng
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 26 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P027
中文名: 蛋白质计算器
本地目录: 027-ing-蛋白质计算器
Git Root: 027-ing-蛋白质计算器/protein-calculator
GitHub Repo: wanghoufan/p027-protein-calculator
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: OK
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: renamed git 在二级目录
```

```text
Project ID: P028
中文名: 酒吧聚会社交导演
本地目录: 028-ing-酒吧聚会社交导演
Git Root: 028-ing-酒吧聚会社交导演
GitHub Repo: wanghoufan/p028-party-night
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 23 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P029
中文名: 图片本地整理
本地目录: 029-ing-图片本地整理项目
Git Root: 029-ing-图片本地整理项目
GitHub Repo: wanghoufan/p029-photo-library-local
Visibility: PRIVATE
Lifecycle: ing
Repo Role: main
Backup Status: DIRTY_WORKTREE
Dirty / Ahead / Behind: 1 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

```text
Project ID: P030
中文名: Skill 日报体系
本地目录: 030-ing-skill 日报体系
Git Root: 030-ing-skill 日报体系
GitHub Repo: wanghoufan/p030-skill-daily
Visibility: PUBLIC
Lifecycle: ing
Repo Role: main
Backup Status: OK
Dirty / Ahead / Behind: 0 / 0 / 0
Last Verified: 2026-09-26
Note: renamed
```

