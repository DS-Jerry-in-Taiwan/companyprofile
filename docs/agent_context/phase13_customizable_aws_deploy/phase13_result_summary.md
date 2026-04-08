## Phase 13: Customizable AWS Deployment - Result Summary

**Changes Made**:
1. 修改 `scripts/deploy_backend.sh` 和 `scripts/deploy_frontend.sh`:
   - 使用 `aws --profile $AWS_PROFILE` 來指定 AWS configure。
   - 使用 `$AWS_REGION` 環境變數設定 region。
2. 更新部署腳本使用說明:
   - 通過設定 `AWS_PROFILE` 和 `AWS_REGION` 環境變數來指定部署的 AWS 環境。
   - 範例:
     ```bash
     AWS_PROFILE=my-prod-config AWS_REGION=us-east-1 ./scripts/deploy_backend.sh prod
     AWS_PROFILE=my-dev-config AWS_REGION=ap-northeast-1 ./scripts/deploy_frontend.sh dev
     ```

**Result**:
部署腳本現在可以靈活地部署到不同的 AWS 環境,無需修改腳本本身。使用者只需在執行時指定對應的 AWS configure 和 region 即可。