# AWS 部署準備總結

## 📊 費用評估結論

### ✅ **答案：不會超過免費額度！**

#### 💰 預估月費用（10,000 次請求）
| 服務 | 費用 | 說明 |
|------|------|------|
| Lambda | **$0.00** | ✅ 100萬次請求/月免費 |
| HTTP API Gateway | **$0.00** | ✅ 前 1200萬次請求免費 |
| ECR (Docker 儲存) | **$0.00** | ✅ 前 12 個月 500MB 免費 |
| CloudWatch Logs | **$0.00** | ✅ 5GB 免費 |
| **Bedrock (Claude API)** | **~$0.33** | ⚠️ 唯一收費項目 |
| **總計** | **~$0.33/月** | 約 **NT$ 10/月** |

#### 📉 不同使用量的費用對照
```
    1,000 次/月 → $0.03  (NT$ 1)
   10,000 次/月 → $0.33  (NT$ 10)   ← 測試階段
  100,000 次/月 → $3.30  (NT$ 100)
1,000,000 次/月 → $33.00 (NT$ 1000)
```

### 🎯 建議
1. ✅ **可以安心部署到您的私人 AWS**
2. ✅ **設定每日請求上限 100 次** → 月費 < NT$ 3
3. ✅ **啟用 AWS Budget 警報** → 超過 $5 通知

詳細費用分析請查看: `docs/deployment/aws_cost_estimation.md`

---

## 🔧 AWS CLI 配置狀態

### 當前狀態
- ✅ **AWS CLI 已安裝**: `aws-cli/2.34.21`
- ⚠️ **需要配置憑證**: Access Key 尚未設定

### 配置步驟
請參考: `docs/deployment/aws_cli_setup.md`

**快速配置**:
```bash
# 1. 執行配置命令
aws configure

# 2. 輸入以下資訊
AWS Access Key ID: <您的 Access Key ID>
AWS Secret Access Key: <您的 Secret Access Key>
Default region: ap-northeast-1
Default output format: json

# 3. 驗證配置
aws sts get-caller-identity
```

---

## 📋 部署前檢查清單

### 已完成 ✅
- [x] 程式碼開發完成
- [x] Docker 映像建立成功
- [x] 本地測試通過
- [x] serverless.yml 配置完成
- [x] AWS CLI 安裝完成
- [x] 費用評估完成

### 待完成 ⏳
- [ ] AWS 憑證配置
- [ ] Serverless Framework 安裝
- [ ] 部署到 AWS dev 環境
- [ ] 部署後驗證測試

---

## 🚀 下一步行動

### 步驟 1: 配置 AWS 憑證 (5 分鐘)
```bash
aws configure
```

### 步驟 2: 安裝 Serverless Framework (2 分鐘)
```bash
npm install -g serverless
```

### 步驟 3: 部署到 AWS (5-10 分鐘)
```bash
serverless deploy --stage dev
```

### 步驟 4: 驗證部署 (2 分鐘)
```bash
# 測試健康檢查
curl https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/health
```

**預估總時間**: 15-20 分鐘

---

## 📚 相關文件

1. **費用評估**: `docs/deployment/aws_cost_estimation.md`
   - 詳細的費用分析
   - 免費額度說明
   - 節省成本建議

2. **AWS CLI 配置**: `docs/deployment/aws_cli_setup.md`
   - 憑證配置步驟
   - 安全建議
   - 疑難排解

3. **本地測試報告**: `docs/agent_context/phase9.1_serverless_flask_deployment/local_test_report.md`
   - Docker 測試結果
   - API 端點驗證
   - 技術實現細節

4. **Checkpoint 1 總結**: `docs/agent_context/phase9.1_serverless_flask_deployment/checkpoint1_summary.md`
   - 程式碼變更總結
   - 架構變更說明
   - 驗證結果

---

## ❓ 常見問題

### Q1: 我的 AWS 帳號是新帳號嗎？
**A**: 如果您在過去 12 個月內註冊，就是新帳號，可享受：
- ECR 500MB 免費儲存
- S3 5GB 免費儲存
- 其他服務的新用戶優惠

### Q2: Bedrock 為什麼要收費？
**A**: Bedrock (Claude API) 是 AI 服務，沒有免費方案。但每次請求只需 $0.000033，非常便宜。

### Q3: 如何限制 Bedrock 使用量？
**A**: 可以在程式碼中加入請求計數器和每日上限：
```python
# 在 api_controller.py
MAX_DAILY_REQUESTS = 100
request_count = 0

@app.route("/v1/company/profile/process", methods=["POST"])
def process_company_profile():
    global request_count
    if request_count >= MAX_DAILY_REQUESTS:
        return jsonify({"error": "每日請求上限"}), 429
    request_count += 1
    # ... 繼續處理
```

### Q4: 測試完成後如何刪除資源？
**A**: 執行以下命令：
```bash
serverless remove --stage dev
```
這會刪除所有 AWS 資源（Lambda、API Gateway、ECR 映像等）。

### Q5: 如何查看實際費用？
**A**: 
1. 登入 AWS Console
2. 前往 **Billing → Bills**
3. 查看當月費用明細

---

## 🎯 總結

### ✅ 可以安心部署的原因
1. 大部分服務都在免費額度內
2. 唯一收費項目 (Bedrock) 費用極低
3. 可以設定請求上限控制費用
4. 可以隨時刪除資源停止計費

### 📝 我已為您準備好
- ✅ 完整的費用評估報告
- ✅ AWS CLI 配置指南
- ✅ 部署檢查清單
- ✅ 疑難排解指南

---

**準備好配置 AWS 憑證了嗎？**

請告訴我您希望如何進行：

1. **選項 A**: 我現在配置 AWS 憑證，然後繼續部署
2. **選項 B**: 我稍後自行配置和部署
3. **選項 C**: 我有其他問題想先確認

請讓我知道您的決定！🚀
