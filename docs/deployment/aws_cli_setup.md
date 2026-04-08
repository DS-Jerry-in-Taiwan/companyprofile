# AWS CLI 配置指南

## 目前狀態
- ✅ **AWS CLI 已安裝**: aws-cli/2.34.21
- ⚠️ **需要配置憑證**

---

## 🔑 配置步驟

### 步驟 1: 取得 AWS Access Key

#### 選項 A: 從 AWS Console 建立新的 Access Key

1. **登入 AWS Console**: https://console.aws.amazon.com/
2. **前往 IAM** → 右上角點擊您的帳號名稱 → **Security credentials**
3. **Access keys** 區塊 → 點擊 **Create access key**
4. **選擇使用案例**: Command Line Interface (CLI)
5. **確認並建立**
6. **下載 .csv 檔案** 或複製以下資訊：
   - Access Key ID (例如: `AKIAIOSFODNN7EXAMPLE`)
   - Secret Access Key (例如: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

#### 選項 B: 使用現有的 Access Key
如果您已經有 Access Key，請準備好以下資訊：
- Access Key ID
- Secret Access Key

---

### 步驟 2: 配置 AWS CLI

#### 方法 1: 互動式配置（推薦）
```bash
aws configure
```

系統會詢問以下資訊：
```
AWS Access Key ID [None]: 輸入您的 Access Key ID
AWS Secret Access Key [None]: 輸入您的 Secret Access Key
Default region name [None]: ap-northeast-1
Default output format [None]: json
```

#### 方法 2: 直接編輯配置檔案
```bash
# 建立 .aws 目錄
mkdir -p ~/.aws

# 編輯憑證檔案
cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
EOF

# 編輯配置檔案
cat > ~/.aws/config << 'EOF'
[default]
region = ap-northeast-1
output = json
EOF
```

**請將以下內容替換為您的實際值**:
- `YOUR_ACCESS_KEY_ID` → 您的 Access Key ID
- `YOUR_SECRET_ACCESS_KEY` → 您的 Secret Access Key

---

### 步驟 3: 驗證配置

```bash
# 檢查配置
aws configure list

# 驗證身份（應該顯示您的帳號資訊）
aws sts get-caller-identity
```

**預期輸出**:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## 🔒 安全建議

### 1. **設定 IAM 使用者權限**
建議建立一個專門用於部署的 IAM 使用者，賦予最小權限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "ecr:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "logs:*",
        "cloudformation:*",
        "s3:*",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. **啟用 MFA (多因素認證)**
- 前往 IAM → Users → Security credentials
- 啟用 MFA 裝置

### 3. **定期輪換 Access Key**
- 建議每 90 天更換一次 Access Key
- 刪除不使用的 Access Key

### 4. **不要將 Access Key 提交到 Git**
確保 `.gitignore` 包含：
```
.aws/
*.pem
*.key
credentials
```

---

## 🚀 配置完成後的下一步

### 安裝 Serverless Framework
```bash
# 使用 npm 安裝
npm install -g serverless

# 驗證安裝
serverless --version
```

### 部署到 AWS
```bash
# 切換到專案目錄
cd /home/ubuntu/projects/OrganBriefOptimization

# 部署到 dev 環境
serverless deploy --stage dev
```

---

## ❓ 疑難排解

### 問題 1: `aws: command not found`
**解決**: 重新載入 PATH
```bash
source ~/.bashrc
# 或
hash -r
```

### 問題 2: `Unable to locate credentials`
**解決**: 檢查憑證檔案
```bash
cat ~/.aws/credentials
cat ~/.aws/config
```

### 問題 3: `Access Denied`
**解決**: 檢查 IAM 使用者權限
```bash
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

---

## 📝 配置檢查清單

部署前請確認：

- [ ] AWS CLI 已安裝 (`aws --version`)
- [ ] Access Key 已配置 (`aws configure list`)
- [ ] 憑證可以驗證 (`aws sts get-caller-identity`)
- [ ] Region 設定為 `ap-northeast-1`
- [ ] IAM 權限包含 Lambda、API Gateway、ECR、Bedrock
- [ ] Serverless Framework 已安裝 (`serverless --version`)
- [ ] `.gitignore` 包含 `.aws/` 和憑證檔案

---

## 🎯 快速配置命令（需要您的 Access Key）

```bash
# 執行此命令後，按照提示輸入您的憑證
aws configure

# 或使用環境變數（臨時）
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 驗證
aws sts get-caller-identity
```

---

**準備好後，請告訴我，我會幫您繼續部署流程！**
