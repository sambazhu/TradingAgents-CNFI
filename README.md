# TradingAgents-CNFI 中文机构增强版

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Repo](https://img.shields.io/badge/GitHub-TradingAgents--CNFI-black.svg)](https://github.com/sambazhu/TradingAgents-CNFI)

面向中文市场研究场景的多智能体股票分析系统。本仓库不是从零开始的新项目，而是我基于 [`hsliuping/TradingAgents-CN`](https://github.com/hsliuping/TradingAgents-CN) 克隆后持续改造的增强版本；其更上游来源是 [`TauricResearch/TradingAgents`](https://github.com/TauricResearch/TradingAgents)。

当前这个公开仓库聚焦于一件事：把原有多智能体分析框架进一步推进到更适合中国金融机构研究流程的形态，因此命名为 **TradingAgents-CNFI**，其中 `CNFI` 表示 **China Financial Institutions**。

## 项目定位

`TradingAgents-CNFI 中文机构增强版` 重点服务以下场景：

- A 股研究与投研辅助
- 中文多智能体分析流程验证
- 机构级数据源接入与富集
- 分析链路可观测、可测试、可排障

这是一个研究与工程实践项目，不构成投资建议，也不承诺任何实盘收益。

## 版本来源

本仓库当前公开版本可以理解为：

- 上游基础框架：`TauricResearch/TradingAgents`
- 中文化与前后端工程化基础：`hsliuping/TradingAgents-CN`
- 本仓库增强基线：基于 `TradingAgents-CN` 的 `v1.0.0-preview` 架构继续改造

也就是说，这个版本保留了原有的 FastAPI + Vue 3 + 多智能体分析主框架，但针对数据源、链路稳定性、前端交互一致性和日志可观测性做了面向中文机构研究场景的增强。

## 本仓库的核心增强

### 1. 恒生聚源数据源接入

这是本次改造里最关键的一项。

系统新增了 `Gildata / 恒生聚源` 数据源能力，并把它接入到了原有分析链路中，用于补强 A 股场景下的数据专业度与可用性。当前仓库里已经可以看到以下相关模块：

- `tradingagents/dataflows/gildata_client.py`
- `tradingagents/dataflows/gildata_enrichment.py`
- `tradingagents/dataflows/gildata_fundamentals.py`
- `tradingagents/dataflows/gildata_news.py`
- `tradingagents/dataflows/gildata_sentiment.py`

这部分增强主要覆盖：

- 基本面补充数据
- 新闻与公告补充数据
- 社媒/情绪侧补充数据
- 技术指标与资金流向富集
- 估值与风险指标补强

目标不是简单“再加一个接口”，而是让恒生聚源真正进入分析报告生成链路，而不是停留在配置层。

同时，这个增强版并没有抛弃原有的 A 股数据基础设施，而是形成了更贴近真实研究场景的组合：

- `Tushare` 继续承担一部分 A 股基础数据与同步能力
- `AkShare` 继续承担公开数据抓取与补充能力
- `BaoStock` 继续作为可选的兼容数据源
- `Gildata / 恒生聚源` 负责更专业的数据富集与机构视角增强

也就是说，本仓库的数据源策略不是“完全替换 Tushare”，而是在保留原有兼容链路的基础上，引入恒生聚源做专业增强。

### 2. 面向 A 股研究的主链路稳定性修复

围绕这轮完整测试，我对主链路做了一批稳定性修复，重点包括：

- 修复分析过程中部分节点长时间卡住或状态不透明的问题
- 修复交易员决策阶段的错误暴露与排障链路
- 修复前端分析进度与 LangGraph 实际节点不同步的问题
- 修复分析日期在 A 股场景下应按 `T-1` 交易日数据处理时的传递偏差
- 梳理 `debug` 与生产运行模式的差异，减少因为调试模式导致的运行不确定性

这些修改的目标是让系统在前端点击测试、后端日志观测、任务状态跟踪三者之间保持一致。

### 3. 分析进度与日志可观测性增强

原系统在“页面显示什么”和“LangGraph 实际跑到哪里”之间存在一定错位。本仓库针对这一点做了增强：

- 按 LangGraph 实际节点映射前端进度文案
- 让分析师、研究员、交易员、风险评估等阶段的进度更加连贯
- 增强调试日志，便于判断当前到底执行到了哪个节点
- 为完整调用链测试补充脚本与排障依据

这类增强的意义在于：当页面显示“研究辩论第 1 轮”或“中性风险评估”时，我们可以更可靠地在后端日志中定位对应节点，而不是只看到一个笼统的 `running`。

### 4. 前端分析配置交互优化

围绕这次真实点击测试，本仓库还对前端分析入口做了若干体验修正：

- 统一了社媒分析师的可选逻辑，不再与右侧选项产生冲突
- 去掉了重复/歧义较大的“情绪分析”独立开关，仅保留风险评估开关
- 让社媒分析师与其他分析师保持同等地位，避免 A 股场景下被误禁用
- 配合 1-5 级分析深度，使前端勾选行为与后端实际分析链路更一致

这部分目标不是单纯改 UI，而是减少“前端看起来选了，后端其实没跑”的认知落差。

### 5. 数据源配置与 Token 处理增强

为了让恒生聚源数据源真正能在系统中稳定启用，我对配置链路也做了增强：

- 支持 `GILDATA_API_TOKEN` 环境变量
- 支持从系统配置中读取 Gildata Token
- 在数据源配置界面中加入 Gildata
- 在默认配置和数据源管理器中加入 Gildata 可用性判断

这使得系统不再只能依赖“代码里写死 token”这种不安全方式，而是具备更合理的配置来源与启停控制。

对于原有数据源，这个版本仍保留并兼容：

- `TUSHARE_TOKEN`
- `TUSHARE_ENABLED`
- `DEFAULT_CHINA_DATA_SOURCE`

因此在本地或 Docker 部署时，如果你希望 A 股基础数据链路更完整，通常仍建议同时配置好 `Tushare`，而把 `Gildata` 作为更高质量的数据增强来源。

## 继承自原项目的基础能力

在保留上述增强的同时，本仓库仍然继承并沿用了 `TradingAgents-CN` 的主要工程能力，包括：

- FastAPI 后端服务
- Vue 3 + Vite 前端
- 多智能体分析流程
- SSE / WebSocket 进度推送
- 报告生成与历史记录
- 多模型供应商接入
- Docker / 本地部署方式

因此更准确地说，这个项目不是推倒重写，而是在已有成熟工程底座上，朝“中文机构增强版”方向继续迭代。

## 当前分析链路概览

一个典型的完整分析任务通常会经过以下阶段：

1. 分析师阶段
2. 研究员辩论阶段
3. 交易员决策阶段
4. 风险评估阶段
5. 最终报告生成

当启用更高分析深度并勾选完整分析师团队时，链路中会包含：

- 市场分析师
- 基本面分析师
- 新闻分析师
- 社媒分析师
- 看涨研究员
- 看跌研究员
- 研究经理
- 交易员
- 激进 / 保守 / 中性风险评估
- 风险经理

而在较低分析深度下，系统会根据预设减少部分分析师或降低辩论/风险评估强度。

## 与原版相比，这个仓库更强调什么

如果用一句话概括差异：

**原版更强调“中文化和完整产品形态”，而这个增强版更强调“机构级数据源接入 + 主链路稳定性 + 真实点击测试与日志可观测性”。**

更具体地说，本仓库的改造方向包括：

- 更专业的 A 股数据富集
- 更清晰的分析调用链验证
- 更容易复盘问题的运行日志
- 更贴近研究场景的前端分析入口逻辑

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/sambazhu/TradingAgents-CNFI.git
cd TradingAgents-CNFI
```

### 2. 准备环境变量

至少需要根据你的模型与数据源配置以下变量：

```bash
DEBUG=false

# 例：DashScope / Qwen / Kimi 兼容接口相关
DASHSCOPE_API_KEY=your_api_key

# A股基础数据（推荐保留）
TUSHARE_TOKEN=your_tushare_token
TUSHARE_ENABLED=true

# 恒生聚源
GILDATA_API_TOKEN=your_gildata_token
```

如果你使用的是数据库中的系统配置，也可以通过前端配置数据源与模型，而不必全部写入环境变量。

### 3. 启动服务

请按仓库中的部署文档选择本地模式或 Docker 模式启动。若你希望先验证服务健康状态，建议优先检查：

- 后端健康接口
- 前端页面是否可正常访问
- 数据源配置是否可读
- 模型供应商配置是否生效

## 建议的验证方式

对于这个增强版，我更推荐用“真实调用链点击测试”而不是只跑单元测试：

- 前端发起一次完整分析
- 观察页面阶段切换是否与预期一致
- 同步观察后端日志
- 确认是否经过预期的分析师、研究员、交易员和风险评估节点
- 最终核对报告里是否包含恒生聚源补充内容

仓库中也保留了一些用于链路验证和数据源验证的脚本，例如：

- `scripts/e2e_frontend_chain_db_gildata.py`
- `scripts/test_gildata_kimi_market.py`
- `scripts/test_full_market_pipeline.py`
- `scripts/test_news_gildata.py`

## 文档与后续计划

仓库内已有较完整的文档与修复记录，可重点查看：

- [docs/](./docs/)
- [docs/fixes/](./docs/fixes/)
- [docs/releases/](./docs/releases/)

接下来这个分支仍会继续沿着以下方向迭代：

- 完善 Gildata 在更多分析节点中的使用深度
- 继续补强新闻/社媒类 A 股数据源
- 让前端阶段展示与 LangGraph 节点更加一一对应
- 持续优化长任务运行时的稳定性与错误恢复能力

## 致谢

感谢以下项目提供的基础工作与灵感：

- [`TauricResearch/TradingAgents`](https://github.com/TauricResearch/TradingAgents)
- [`hsliuping/TradingAgents-CN`](https://github.com/hsliuping/TradingAgents-CN)

本仓库是基于前述项目继续演化的个人增强版本。这里的增强与维护工作，主要聚焦在中文机构研究场景的数据、流程与工程稳定性上。

## 免责声明

本项目仅用于学习、研究、工程验证与投研辅助，不构成任何投资建议。股票市场存在风险，任何模型输出、自动化分析结果和生成报告都应由使用者自行复核。
