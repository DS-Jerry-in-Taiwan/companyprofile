# 監控設定（Phase 5）

此文件說明如何在最小範圍內啟用效能/成本監控，方便在 MVP 期間觀察系統行為。

1. 日誌位置
- Audit log: `logs/risk_audit.log`（JSONL）
- Token / cost CSV: `logs/token_costs.csv`
- Perf logs: `logs/perf_logs.csv`

2. 最小監控方案
- 使用 `scripts/token_cost_logger.py` 與 `scripts/perf_timer.py` 收集資料，定期匯出 CSV。
- 用簡單的 Prometheus + Grafana 或直接將 CSV 匯入到監控面板。

3. 建議指令
```bash
# 即時檢視最近的 audit event
tail -n 50 logs/risk_audit.log

# 檢視 token cost summary
python scripts/perf_analysis.py
```

4. 告警建議
- 當單日 token 成本超過預算 Notify（Slack / Email）
- 當 review_queue 數量短時間暴增（例如 100 件/小時）則觸發告警
