# 部署快速參考卡

## 🚀 快速命令

### 部署到不同環境

```bash
# 開發環境（東京）
./scripts/deploy_backend.sh -s dev -r ap-northeast-1

# 測試環境（美國東部）
./scripts/deploy_backend.sh -s staging -r us-east-1

# 生產環境（東京）
./scripts/deploy_backend.sh -s prod -r ap-northeast-1 -p prod-account

# 乾跑測試（只查看不執行）
./scripts/deploy_backend.sh -s dev --dry-run
```

## ⚙️ 環境配置

### 初始化環境

```bash
# 初始化開發環境（引導式）
./scripts/config_manager.sh init dev

# 查看環境配置
./scripts/config_manager.sh show dev

# 設置單個 API Key
./scripts/config_manager.sh set dev google-genai-api-key sk-xxx
```

## 🔍 診斷命令

```bash
# 驗證 AWS 配置
aws sts get-caller-identity

# 查看可用環境
./scripts/config_manager.sh list

# 驗證 Dockerfile 配置
./scripts/validate_lambda_setup.sh

# 檢查 Lambda 函數
aws lambda get-function --function-name organ-brief-optimization-dev-flaskApi

# 查看實時日誌
aws logs tail /aws/lambda/organ-brief-optimization-dev-flaskApi --follow
```

## 📋 部署前檢查清單

```bash
☐ aws sts get-caller-identity  # 驗證 AWS 配置
☐ ./scripts/validate_lambda_setup.sh  # 驗證部署配置
☐ ./scripts/config_manager.sh show dev  # 檢查參數
☐ ./scripts/deploy_backend.sh -s dev --dry-run  # 乾跑測試
☐ 確認無誤後執行實際部署
```

## 🆘 常見問題快速解決

| 問題 | 解決方案 |
|------|--------|
| **AWS CLI 未配置** | `aws configure` |
| **缺少 API Keys** | `./scripts/config_manager.sh init dev` |
| **ECR 登入失敗** | 重新運行部署腳本，它會重新登入 |
| **部署超時** | 等待幾分鐘再試，或檢查 CloudFormation 狀態 |
| **Docker 未運行** | `systemctl start docker` (Linux) 或啟動 Docker Desktop |

## 📊 部署選項速查表

| 選項 | 簡寫 | 用途 | 例子 |
|------|------|------|------|
| `--stage` | `-s` | 指定環境 | `-s prod` |
| `--region` | `-r` | 指定區域 | `-r us-east-1` |
| `--profile` | `-p` | 指定 AWS Profile | `-p prod-account` |
| `--dry-run` | - | 乾跑模式 | `--dry-run` |
| `--skip-validate` | - | 跳過驗證 | `--skip-validate` |
| `--skip-login` | - | 跳過 ECR 登入 | `--skip-login` |
| `--help` | `-h` | 顯示幫助 | `-h` |

## 🌍 AWS 區域代碼

| 區域 | 代碼 | 特點 |
|------|------|------|
| 東京 | `ap-northeast-1` | 台灣最低延遲 ⭐ |
| 新加坡 | `ap-southeast-1` | 亞洲備選 |
| 美國東部 | `us-east-1` | 全球最便宜 |
| 歐洲 | `eu-west-1` | 歐洲用戶最優 |

## 📱 相關資源

- 📖 [完整部署指南](./docs/DEPLOYMENT_GUIDE.md)
- 🔧 [部署腳本](./scripts/deploy_backend.sh)
- ⚙️ [配置管理器](./scripts/config_manager.sh)
- ✅ [驗證腳本](./scripts/validate_lambda_setup.sh)

## 💡 提示

- 🔓 避免在命令行中傳遞密鑰，使用 `--profile` 和 Parameter Store
- 🧪 總是先用 `--dry-run` 測試
- 📍 為不同環境使用不同的 AWS Profiles
- ⏱️ 在低流量時段部署生產環境
- 📝 部署後立即檢查日誌

---

**最後更新：** 2026-04-13
