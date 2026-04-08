# 文件索引

本文檔提供專案中所有開發文件的索引，幫助快速找到所需的技術文檔、開發記錄和配置說明。

---

## 目錄結構總覽

```
docs/
├── agent_config/              # Agent 開發配置與工作流程
├── agent_context/             # 開發階段上下文與交付記錄
├── api/                       # API 規格與 schema 文件
├── architecture/              # 架構設計與系統分析
├── deployment/                # 部署相關文件
├── diagrams/                  # 流程圖與圖片
├── guides/                    # 使用指南
├── operations/                # 運維相關文件
├── quality/                   # 品質評估與測試報告
├── reports/                   # 各種報告
├── research/                  # 研究與搜尋策略分析
├── releases/                  # 版本發布記錄
├── troubleshooting/           # 調試與問題排除
├── templates/                 # Prompt 模板
└── index.md                   # 本文件
```

---

## 🔧 Agent 開發配置

| 文件 | 說明 |
|------|------|
| [agent_config/AGENTS.md](./agent_config/AGENTS.md) | Agent 角色定義與職責 |
| [agent_config/INSTRUCTION.md](./agent_config/INSTRUCTION.md) | Agent 開發指令 |
| [agent_config/multi_agent_dev_workflow_v4.0.md](./agent_config/multi_agent_dev_workflow_v4.0.md) | 多 Agent 開發工作流 v4.0 |
| [agent_config/mvp_company_profile_api.yml](./agent_config/mvp_company_profile_api.yml) | MVP API 規格 (YAML) |

---

## 📋 開發階段記錄

按開發階段組織的完整上下文、交付記錄和檢查點。

### Phase 1 - 基礎建設

| 文件 | 說明 |
|------|------|
| [agent_context/phase1/00_phase_overview.md](./agent_context/phase1/00_phase_overview.md) | Phase 1 總覽 |
| [agent_context/phase1/01_dev_goal_context.md](./agent_context/phase1/01_dev_goal_context.md) | 開發目標 |
| [agent_context/phase1/02_dev_flow_context.md](./agent_context/phase1/02_dev_flow_context.md) | 開發流程 |
| [agent_context/phase1/03_agent_roles_context.md](./agent_context/phase1/03_agent_roles_context.md) | Agent 角色 |
| [agent_context/phase1/04_agent_prompts_context.md](./agent_context/phase1/04_agent_prompts_context.md) | Agent Prompt |
| [agent_context/phase1/05_validation_checklist.md](./agent_context/phase1/05_validation_checklist.md) | 驗證清單 |
| [agent_context/phase1/06_delivery_record.md](./agent_context/phase1/06_delivery_record.md) | 交付記錄 |
| [agent_context/phase1/07_checkpoint_protocol.md](./agent_context/phase1/07_checkpoint_protocol.md) | 檢查點協議 |

### Phase 2 - 搜尋與數據處理

| 文件 | 說明 |
|------|------|
| [agent_context/phase2/](./agent_context/phase2/) | Phase 2 完整文件 |

### Phase 3 - 風險控制

| 文件 | 說明 |
|------|------|
| [agent_context/phase3/](./agent_context/phase3/) | Phase 3 完整文件 |

### Phase 4 - 品質優化

| 文件 | 說明 |
|------|------|
| [agent_context/phase4/](./agent_context/phase4/) | Phase 4 完整文件 |

### Phase 5 - 測試與監控

| 文件 | 說明 |
|------|------|
| [agent_context/phase5/CHANGELOG_PHASE5.md](./agent_context/phase5/CHANGELOG_PHASE5.md) | Phase 5 變更日誌 |
| [agent_context/phase5/](./agent_context/phase5/) | Phase 5 完整文件 |

### Phase 6-9 - 前端與部署

| Phase | 目錄 | 說明 |
|-------|------|------|
| Phase 6 | [agent_context/phase6_frontend_demo/](./agent_context/phase6_frontend_demo/) | 前端示範 |
| Phase 7 | [agent_context/phase7_frontend_visual_refactor/](./agent_context/phase7_frontend_visual_refactor/) | 前端視覺重構 |
| Phase 8 | [agent_context/phase8_e2e_process_improvement/](./agent_context/phase8_e2e_process_improvement/) | E2E 流程改進 |
| Phase 9 | [agent_context/phase9_langchain_integration/](./agent_context/phase9_langchain_integration/) | LangChain 整合 |
| Phase 9.1 | [agent_context/phase9.1_serverless_flask_deployment/](./agent_context/phase9.1_serverless_flask_deployment/) | Serverless 部署 |
| Phase 10 | [agent_context/phase10_search_optimization/](./agent_context/phase10_search_optimization/) | 搜尋優化 (進行中) |

---

## 🏗️ 架構設計

| 文件 | 說明 |
|------|------|
| [architecture/ARCHITECTURE_ANALYSIS_REPORT.md](./architecture/ARCHITECTURE_ANALYSIS_REPORT.md) | 架構分析報告 |
| [architecture/architecture_flow.md](./architecture/architecture_flow.md) | 架構流程圖 |
| [architecture/OPTIMIZATION_STRATEGY.md](./architecture/OPTIMIZATION_STRATEGY.md) | 優化策略 |
| [architecture/search_pipeline_diagram.md](./architecture/search_pipeline_diagram.md) | 搜尋管線圖 |
| [architecture/risk_control_flow_diagram.md](./architecture/risk_control_flow_diagram.md) | 風險控制流程圖 |

---

## 🔍 搜尋與研究

| 文件 | 說明 |
|------|------|
| [research/SEARCH_STRATEGY_REFINED.md](./research/SEARCH_STRATEGY_REFINED.md) | 精煉後的搜尋策略 |
| [research/SEARCH_IMPLEMENTATION_SUMMARY.md](./research/SEARCH_IMPLEMENTATION_SUMMARY.md) | 搜尋實現摘要 |
| [research/SEARCH_COMPARISON.md](./research/SEARCH_COMPARISON.md) | 搜尋工具比較 |
| [research/data_retrieval_flowcharts.md](./research/data_retrieval_flowcharts.md) | 數據檢索流程圖 |
| [agent_context/phase10_search_optimization/01_discussion_summary.md](./agent_context/phase10_search_optimization/01_discussion_summary.md) | 搜尋優化討論彙整 |

---

## 📊 品質評估

| 文件 | 說明 |
|------|------|
| [quality/quality_thresholds.md](./quality/quality_thresholds.md) | 品質閾值定義 |
| [quality/quality_decision_tree.md](./quality/quality_decision_tree.md) | 品質決策樹 |
| [quality/final_quality_report.md](./quality/final_quality_report.md) | 最終品質報告 |
| [quality/quality_assessment_report.md](./quality/quality_assessment_report.md) | 品質評估報告 |
| [quality/README_QUALITY_ASSESSMENT.md](./quality/README_QUALITY_ASSESSMENT.md) | 品質評估說明 |

---

## 📚 使用指南

| 文件 | 說明 |
|------|------|
| [guides/IMPLEMENTATION_GUIDE.md](./guides/IMPLEMENTATION_GUIDE.md) | 實現指南 |
| [guides/QUICK_START.md](./guides/QUICK_START.md) | 快速開始 |
| [guides/migration_plan_google_genai.md](./guides/migration_plan_google_genai.md) | Google GenAI 遷移計劃 |

---

## 📊 報告與數據

| 文件 | 說明 |
|------|------|
| [reports/phase2_summary_report.md](./reports/phase2_summary_report.md) | Phase 2 摘要報告 |
| [reports/test_analysis_report.md](./reports/test_analysis_report.md) | 測試分析報告 |
| [reports/security_audit_report.md](./reports/security_audit_report.md) | 安全審計報告 |
| [reports/final_test_report.csv](./reports/final_test_report.csv) | 最終測試數據 |

---

## 🚀 部署與營運

| 文件 | 說明 |
|------|------|
| [deployment/aws_cli_setup.md](./deployment/aws_cli_setup.md) | AWS CLI 設定 |
| [deployment/aws_cost_estimation.md](./deployment/aws_cost_estimation.md) | AWS 成本估算 |
| [deployment/backend_deployment.md](./deployment/backend_deployment.md) | 後端部署指南 |
| [deployment/deployment_summary.md](./deployment/deployment_summary.md) | 部署摘要 |
| [operations/monitoring_setup.md](./operations/monitoring_setup.md) | 監控設定 |

---

## 📦 版本發布

| 文件 | 說明 |
|------|------|
| [releases/phase4_mvp_release.md](./releases/phase4_mvp_release.md) | Phase 4 MVP 發布 |
| [releases/phase5_mvp_release.md](./releases/phase5_mvp_release.md) | Phase 5 MVP 發布 |
| [releases/CHANGELOG_PHASE5.md](./releases/CHANGELOG_PHASE5.md) | Phase 5 變更日誌 |

---

## 🔌 API 規格

| 文件 | 說明 |
|------|------|
| [api/organbrief-api.yml](./api/organbrief-api.yml) | OpenAPI 規格 (YAML) |
| [api/api_schema_v2.md](./api/api_schema_v2.md) | API Schema v2 |

---

## 🔧 調試與問題排除

| 文件 | 說明 |
|------|------|
| [troubleshooting/debug_mock_modules.md](./troubleshooting/debug_mock_modules.md) | 調試與 Mock 模組 |

---

## 🖼️ 流程圖

| 文件 | 說明 |
|------|------|
| [diagrams/404_process.png](./diagrams/404_process.png) | 404 處理流程圖 |
| [diagrams/demand_flow.png](./diagrams/demand_flow.png) | 需求流程圖 |
| [diagrams/demo_frontend.png](./diagrams/demo_frontend.png) | 前端示範截圖 |

---

## 🏷️ 主題索引

### 搜尋相關
- `research/SEARCH_*.md`
- `architecture/search_pipeline_diagram.md`
- `agent_context/phase10_search_optimization/`

### 品質相關
- `quality/*.md`

### 部署相關
- `deployment/*.md`
- `operations/*.md`
- `agent_context/phase9*.md`

### 前端相關
- `agent_context/phase6_frontend_demo/`
- `agent_context/phase7_frontend_visual_refactor/`

### 報告相關
- `reports/*.md`
- `reports/*.csv`

---

*最後更新: 2026-04-08*
