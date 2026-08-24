# Data And Quant

统一的统计学习、量化数据工程、因子研究、组合、回测、执行、风险和市场结构 Skill 集合。

## 入口

广义、模糊、跨领域或端到端任务从 `SKILL.md`（`data-quant-hybrid`）进入。明确的单领域任务可以直接使用子 Skill：

- `statistical-learning-analysis`：统计学习方法选择、验证和通用诊断。
- `factor-quant-analysis`：股票因子、实证资产定价、A 股和 Smart Beta。
- `quant-trading-black-box-analysis`：策略组件、成本、组合、执行、HFT、风险和经理尽调。

- `quant-data-engineering`：标准表、证券主数据、交易日历、PIT、复权、标签和血缘。

- `futures-quant-analysis`：期货合约、换月、结算、保证金和基差。
- `options-volatility-analysis`：期权链、IV、Greeks、对冲和波动率策略。
- `fixed-income-quant-analysis`：债券现金流、曲线、久期凸性和信用风险。
- `fx-quant-analysis`：外汇报价、远期、套息、结算和币种归因。
- `crypto-quant-analysis`：现货/永续、资金费率、清算、交易所和链上时序。

## 本地运行

```bash
python3 -m pip install -e '.[all,dev]'
quantctl doctor
quantctl list-capabilities
quantctl validate-manifest examples/manifests/minimal.yaml
quantctl run examples/manifests/factor-research.yaml
bash scripts/full_check.sh
```

未传 `quantctl run --output` 时，相对 `output_dir` 会写到 `DATA_QUANT_RUN_ROOT`；若未设置，则使用 `${XDG_STATE_HOME:-~/.local/state}/data-quant`。运行目录位于 Skill 源树内会被拒绝。Manifest 原生路径已覆盖 data、research、validation、portfolio、offline execution、risk、monitoring、governance 和 report；未声明可执行诊断的阶段不会静默通过。

完整 Skill 源 Bundle 与 runtime-only `data-quant-core` wheel 的内容、能力可用性及独立版本规则见 [distribution contract](references/distribution.md)。

机器契约位于 `schemas/`（包括 canonical tables 与 32 项 native diagnostic 参数 Schema），共享运行时代码位于 `src/data_quant/`，完整 Python 3.14 测试环境及 wheel hashes 记录在 `pylock.toml`。原生 `data_quant.backtest.run_portfolio_backtest` 仅执行离线向量化诊断：强制完整 execution/return 窗口、单一 simple/gross/total-return label、非重叠区间和币种一致，并应用显式 flat cash/financing/short-borrow rates，或对实际持有期使用 bounded PIT cash/financing curve interpolation；配套 `portfolio-eligibility` 审计 PIT universe、公司行动窗口和 borrow flag，但仍不声称 locate 数量、recall、市场冲击或实际成交；`execution-replay` 只对 canonical orders/quotes 做确定性离线回放，支持 market/limit、GTC/DAY/IOC、expiry、部分成交和 arrival/VWAP shortfall；`rebalance-replay` 可从 current/target weights 生成受 lot、minimum notional 与 quote participation 约束的离线订单，但二者都不声称队列优先级或市场冲击保真。`RunManifest.execution` 不接受 live、broker、资金划转或凭据存储配置。所有生成结果必须写到源码目录之外的运行目录。

## 证据与安全边界

- 结论优先级：可观察时间 > universe/可交易性 > 执行 > 净值 > OOS/live > 风险/容量 > 机制 > 显著性 > in-sample fit。
- 缺少 point-in-time、成本、可交易性或执行证据时不得升级为 paper/production candidate。
- 本集合只做研究、离线仿真、回放、监控和审计；不实盘下单、不划转资金、不保存凭据。
