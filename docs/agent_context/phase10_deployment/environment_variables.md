# 環境變數設定

## 後端環境變數

### Lambda 環境變數

| 變數名稱 | 說明 | 範例值 |
|----------|------|--------|
| `STAGE` | 部署階段 | `dev`, `staging`, `prod` |
| `BEDROCK_REGION` | AWS Bedrock 區域 | `ap-northeast-1` |
| `CLAUDE_MODEL_ID` | Claude 模型 ID | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `CORS_ORIGINS` | 允許的來源網域（逗號分隔） | `https://your-domain.com` |

### 本地開發 .env

```env
# AWS 設定
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock 設定
BEDROCK_REGION=ap-northeast-1
CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# 應用設定
STAGE=dev
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# 日誌設定
LOG_LEVEL=DEBUG
```

---

## 前端環境變數

### Vite 環境變數（必須以 VITE_ 開頭）

| 變數名稱 | 說明 | 範例值 |
|----------|------|--------|
| `VITE_API_BASE_URL` | API 基礎路徑 | `https://api.example.com` |

### 本地開發 .env.development

```env
VITE_API_BASE_URL=/api
```

### 生產環境 .env.production

```env
VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod
```

---

## Serverless Framework 環境變數

### 使用 AWS Systems Manager Parameter Store

```yaml
provider:
  environment:
    DB_PASSWORD: ${ssm:/organ-brief/${self:provider.stage}/db-password}
```

### 使用 dotenv

```yaml
custom:
  dotenv:
    path: .env.${self:provider.stage}

provider:
  environment:
    SOME_VAR: ${env:SOME_VAR}
```

---

## IAM 權限

### Lambda 執行角色權限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## 安全建議

1. **不要將 .env 檔案提交到版本控制**
2. **使用 IAM 角色而非存取金鑰**
3. **定期輪換金鑰**
4. **使用 Parameter Store 或 Secrets Manager 儲存敏感資訊**
5. **限制 CORS 來源網域**
