# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

本仓库是一个 **Agent Skill 包**（不是应用程序），位于 `10-data-quant/statistical-learning-analysis/`,提供端到端统计学习与量化金融分析的方法选择与诊断能力。它由 Claude/Codex 等代理通过 `SKILL.md` 加载,并按需读取 `references/` 文档与运行 `scripts/` 工具。

仓库**包含** `requirements.txt`、`requirements-optional.txt`、`examples/` demo 数据与 shell,以及 `scripts/_check_skill_index.py` 索引校验工具。**不包含**构建系统、`package.json`、测试目录或 CI 配置。改动的对象主要是 Markdown 文档和独立 Python 脚本。

## 常用命令

### 安装依赖
仓库现在依赖 numpy/pandas/scipy(必选)与 scikit-learn/joblib(可选):
```bash
cd 10-data-quant/statistical-learning-analysis
pip install -r requirements.txt
pip install -r requirements-optional.txt   # 仅 sklearn_tabular_model.py + cluster_quality_report.py 需要
pip install -r requirements-dev.txt        # upstream skill quick_validate 需要 PyYAML
```

### 运行任意脚本
绝大多数脚本依赖 **numpy + pandas (+ scipy)**;另有 9 个统计学习起步工具仍仅依赖标准库(profile_dataset、split_dataset、causal_balance_check、time_series_backtest、classification_report、threshold_tuning、missingness_report、panel_summary、compare_model_reports):
```bash
cd 10-data-quant/statistical-learning-analysis/scripts
python3 <脚本名>.py --help              # 查看参数
python3 profile_dataset.py path/to.csv   # CSV 第一遍画像
```

### 端到端 demo
仓库包含 3 条 demo 链路,合成数据 + shell 串联,首次运行会自动生成数据:
```bash
cd 10-data-quant/statistical-learning-analysis
bash examples/run_alpha_pipeline.sh        # factor_ic → incremental_alpha → alpha_research_gate
bash examples/run_portfolio_pipeline.sh    # portfolio_backtest → portfolio_construction_gate
bash examples/run_nonquant_examples.sh     # 生存 / 异常 / 聚类 / 校准
```

### 量化脚本共享辅助模块
`scripts/quant_utils.py` 已重写为 numpy/pandas/scipy 内核,提供 `read_dataframe`、`require_columns`、`ols`(SVD-based)、`newey_west_se`、`solve_psd`、`summarize_series`、`summarize_returns`、`max_drawdown`、`cross_sectional_corr`、`rank_within` 等,同时保留 `parse_float`/`is_missing`/`mean`/`stdev`/`quantile`/`correlation`/`spearman`/`sorted_group_keys`/`summarize_values`(别名)等标量便捷接口供 row-by-row 审计脚本使用。被约 50 个脚本通过 `from quant_utils import ...` 引用(非包,无 `__init__.py`)。**必须从 `scripts/` 目录执行**,或确保该目录在 `sys.path` 上。

### 索引校验
新增 `scripts/_check_skill_index.py`(下划线前缀=内部脚本),核对 SKILL.md / implementation-map.md / scripts/ / references/ 四方一致:
```bash
python3 scripts/_check_skill_index.py    # 退出码非零即不一致
```

### Smoke 验证
`scripts/smoke_check.sh` 是当前标准验证入口。quick 模式只依赖标准库;full 模式要求 requirements / requirements-optional / requirements-dev 全部已安装,并会跑官方 skill quick_validate 与三条 example pipeline:
```bash
bash scripts/smoke_check.sh --quick
bash scripts/smoke_check.sh --full
```

### 输出格式约定
大多数脚本支持:
```bash
python3 <script>.py <input>.csv --format markdown        # 默认,stdout
python3 <script>.py <input>.csv --format json
python3 <script>.py <input>.csv --output-json out.json --output-md out.md
```

### Quant 报告链(JSON 管线)
许多量化脚本产出 JSON 给下游 gate / aggregator 消费,形成一条链:
- 单项诊断脚本(`factor_ic_report.py`、`incremental_alpha_report.py`、`portfolio_backtest.py` 等)→ JSON
- gate 脚本(`alpha_research_gate_report.py`、`portfolio_construction_gate_report.py`、`go_live_gate_report.py`)消费多份 JSON 产出 pass/review/fail 决策
- `quant_report_aggregator.py` 与 `quant_review_pack.py` 合成 JSON 形成评审包

要复现完整链路:先跑诊断脚本写出 JSON → 把多个 JSON 路径作为参数喂给 gate/aggregator。

## 架构

### 三层文档参考路径
代理被 SKILL.md 引导按以下顺序读文档(不要打乱):

1. **路由层** — `references/decision-tree.md`:从用户的「声明类型」(预测/解释/因果/分群/异常/生存/预测/排序)和「目标形态」路由到方法家族。
2. **候选层** — `references/method-map.md`:列出方法家族与适用场景。
3. **原理层** — `references/principles.md`:核心思想、假设、常见误用,用于解释/比较/诊断。

支撑层(按需读):`playbooks.md`(场景化工作流)、`evaluation-checklist.md`(验证/指标/诊断)、`anti-patterns.md`(常见错误)、`implementation-map.md`(代码/库映射,仅当用户要代码时)、`report-templates.md`(交付模板)、`glossary-zh-en.md`(中英术语)。
JSON 管线或 gate/aggregator 改动还要读 `references/output-contracts.md`,保持字段向后兼容。

### Quant 子体系(自成完整路径)
量化金融部分有平行的五份文档,在任务涉及资产收益/因子/风险/组合/回测/上线时**必读**:
- `quant-finance.md`(方法地图)
- `quant-method-principles.md`(原理与失败模式)
- `quant-anti-patterns.md`(失败案例)
- `quant-production-monitoring.md`(纸面/实盘监控、go-live、退役)
- `quant-report-templates.md`(交付物模板)

### Scripts 的三类目的
1. **统计学习起步工具**(标准库):`profile_dataset.py`、`split_dataset.py`、`classification_report.py`、`threshold_tuning.py`、`missingness_report.py`、`panel_summary.py`、`compare_model_reports.py`、`causal_balance_check.py`、`time_series_backtest.py`。`sklearn_tabular_model.py` 需 scikit-learn。
2. **量化诊断/审计/网关**(numpy + pandas [+ scipy]):涵盖因子诊断(IC、分位、衰减、换手)、组合(回测、约束、暴露、风险贡献)、执行(成本、滑点、容量、可交易性)、风险(波动率、VaR 校准、模型风险登记册)、生产监控(信号健康、live vs paper、限额突破、订单异常、数据新鲜度)、上线网关(`alpha_research_gate_report.py`、`portfolio_construction_gate_report.py`、`go_live_gate_report.py`)、审查包(`quant_review_pack.py`)。
3. **方法补全**(numpy + pandas + scipy / sklearn):`survival_km_report.py`(KM + log-rank)、`anomaly_score_report.py`(z-score/IQR/Mahalanobis)、`cluster_quality_report.py`(silhouette + bootstrap ARI,需 sklearn)、`calibration_report.py`(可靠性曲线 + ECE + Brier)。

### SKILL.md 索引一致性约束
SKILL.md 同时充当:① skill 元数据(顶部 YAML frontmatter)、② 工作流脚本(步骤 1-19)、③ scripts 与 references 的**人工维护索引**(双份列表,既在 `## Scripts` 段又在 `## References` 段)。

**添加新脚本时必须同步**:
- 在 SKILL.md 的 `## Scripts` 段加一行描述
- 在 SKILL.md 的 `## References` 段加一行带链接
- 在 `references/implementation-map.md` 的 "Bundled Scripts" 表内加行
- (量化脚本同时考虑是否在 `quant-finance.md` 末尾的脚本列表中加入)

**添加新 reference 文档时**:在 SKILL.md 的 `## References` 段加入,并在 `## Core Workflow` 步骤列表中插入"何时读它"的指引。

跑 `python3 scripts/_check_skill_index.py` 即可在落 commit 前自动捕捉漏索引(返回非零退出码)。
正式交付前优先跑 `bash scripts/smoke_check.sh --quick`;依赖齐全时跑 `bash scripts/smoke_check.sh --full`。

## 代码风格约定

- 所有脚本以 `#!/usr/bin/env python3` 起始(便于直接执行),使用 `from __future__ import annotations`。
- 文件顶端有 docstring,声明用途与依赖范围。
- CLI 一律用 `argparse`,**不要**引入 `click`/`typer`。
- CSV 读取走 `quant_utils.read_dataframe`(内部 `pd.read_csv(..., encoding="utf-8-sig")`)。仅 9 个标准库起步工具继续使用 `csv.DictReader` + `csv.Sniffer`,不要扩散到新脚本。
- 数值列在 DataFrame 路径里用 `pd.to_numeric(..., errors="coerce")`,缺失值由 pandas 自身的 NaN 处理。row-by-row 审计路径仍可用 `quant_utils.parse_float`/`is_missing`(`MISSING={"", "na", "n/a", "nan", "null", "none", "."}`)。
- 线性代数走 numpy/scipy:OLS 用 `quant_utils.ols`(SVD-based `np.linalg.lstsq` + QR 协方差);HAC SE 用 `quant_utils.newey_west_se`;PSD 解线性方程组用 `quant_utils.solve_psd`(Cholesky)。**不要**重写手动 Gauss-Jordan/三重循环矩阵乘。
- **不要**给已存在于 `quant_utils.py` 的能力另起炉灶。

## SKILL.md 工作流的"硬约束"

SKILL.md 中的 Guardrails 与 Output Contract 是代理行为契约,**修改 SKILL.md 时不要弱化**:
- 预处理/重采样/特征选择/插补禁止在 CV 折之外做
- 时序、生存、面板数据禁止随机切分
- 不可在不平衡分类只看 accuracy
- 不可把 t-SNE/UMAP 当作可分性证据
- 用户要推断/系数/区间时不可只给黑盒模型
- 严格区分关联/预测/干预/反事实

## 改动建议

- **加新方法**:同时更新 method-map.md(候选)、principles.md(原理)、anti-patterns.md(若有典型误用);若涉及实现,更新 implementation-map.md。
- **加新诊断脚本**:沿用 `quant_utils.py` 与 argparse 模式;若产生 JSON 输出且可被 gate 消费,考虑接入 `alpha_research_gate_report.py` 或 `portfolio_construction_gate_report.py` 的 `DEFAULT_REQUIRED_TYPES` 或 `quant_report_aggregator.py` 的 `COMMON_METRIC_PATHS`。
- **scripts/ 内部不要建子目录**:当前所有脚本平铺,辅助模块靠相对导入 `from quant_utils import ...`,改成包结构会破坏现有调用方式。
