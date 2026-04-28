## Phase 13: Customizable AWS Deployment

**Goal**:
- 修改現有的部署腳本,使之能夠根據使用者指定的 AWS configure 來部署到不同的 AWS 環境。

**Planned Changes**:
1. 修改 `scripts/deploy_backend.sh` 和 `scripts/deploy_frontend.sh` 兩個部署腳本:
   - 使用 `aws --profile $AWS_PROFILE` 來指定使用哪個 AWS configure。
   - 將 S3 bucket 名稱和 region 也改為使用環境變數 `$AWS_REGION`。
2. 更新相關文檔,說明如何使用這些修改後的部署腳本。

**Deliverables**:
- 修改後的部署腳本
- 使用說明文件 (phase13_result_summary.md)