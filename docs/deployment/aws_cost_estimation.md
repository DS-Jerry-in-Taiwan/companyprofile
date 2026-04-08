# AWS 部署成本評估報告

## 評估日期
2026-04-01

## 評估對象
**OrganBrief Optimization API** - Flask + Lambda + HTTP API Gateway 架構

---

## 🆓 AWS 免費方案 (Free Tier) 總覽

### 永久免費
這些服務在免費方案下**永久免費**（不限於 12 個月）：

| 服務 | 免費額度 | 超出費用 |
|------|---------|---------|
| **Lambda 請求** | 100萬次/月 | $0.20 / 100萬次 |
| **Lambda 運算** | 40萬 GB-秒/月 | $0.0000166667 / GB-秒 |
| **CloudWatch Logs** | 5 GB 存儲 | $0.50 / GB |
| **CloudWatch Logs 擷取** | 5 GB / 月 | $0.50 / GB |

### 前 12 個月免費
這些服務在新帳號的**前 12 個月免費**：

| 服務 | 免費額度 | 超出費用 |
|------|---------|---------|
| **ECR 儲存** | 500 MB / 月 | $0.10 / GB |
| **S3 儲存** | 5 GB 標準儲存 | $0.023 / GB |
| **S3 請求** | 20,000 GET, 2,000 PUT | $0.0004 / 1000 GET |

### HTTP API Gateway (不在免費方案內)
| 服務 | 費用 |
|------|-----|
| **HTTP API Gateway** | **前 1200萬次請求免費** |
| 超出後 | $1.00 / 100萬次 (ap-northeast-1) |

---

## 📊 本專案預估成本

### 假設使用量（測試/開發階段）

| 項目 | 每月使用量 | 計算 |
|------|-----------|------|
| API 請求數 | 10,000 次 | 輕度測試 |
| 平均執行時間 | 2 秒 / 請求 | Claude API 調用 |
| Lambda 記憶體 | 1024 MB (1 GB) | serverless.yml 配置 |
| Docker 映像大小 | ~400 MB | 實際測量 |
| 日誌量 | ~500 MB / 月 | 結構化日誌 |

---

### 💰 費用明細（每月）

#### 1. **AWS Lambda**
```
請求次數: 10,000 次/月
✅ 免費額度: 1,000,000 次/月
💵 費用: $0.00 (在免費額度內)

運算時間:
- 執行時間: 10,000 次 × 2 秒 = 20,000 秒
- GB-秒: 20,000 秒 × 1 GB = 20,000 GB-秒
✅ 免費額度: 400,000 GB-秒/月
💵 費用: $0.00 (在免費額度內)
```

#### 2. **HTTP API Gateway**
```
請求次數: 10,000 次/月
✅ 免費額度: 12,000,000 次/月 (前 1200萬次)
💵 費用: $0.00 (在免費額度內)
```

#### 3. **Amazon ECR (Docker 映像儲存)**
```
儲存空間: ~400 MB
✅ 免費額度: 500 MB/月 (前 12 個月)
💵 費用: $0.00 (在免費額度內)

注意: 12 個月後收費
- 超出 500 MB 部分: $0.10/GB/月
- 400 MB ≈ $0.04/月
```

#### 4. **Amazon Bedrock (Claude API)**
```
⚠️ Bedrock 沒有免費方案！

Claude 3.5 Sonnet 定價 (ap-northeast-1):
- 輸入: $3.00 / 100萬 tokens
- 輸出: $15.00 / 100萬 tokens

假設每次請求:
- 輸入: 1,000 tokens (公司簡介)
- 輸出: 2,000 tokens (優化結果)

10,000 次請求:
- 輸入成本: (10,000 × 1,000 / 1,000,000) × $3.00 = $0.03
- 輸出成本: (10,000 × 2,000 / 1,000,000) × $15.00 = $0.30
💵 費用: $0.33/月
```

#### 5. **CloudWatch Logs**
```
日誌擷取: 500 MB/月
✅ 免費額度: 5 GB/月
💵 費用: $0.00 (在免費額度內)

日誌儲存: 500 MB
✅ 免費額度: 5 GB
💵 費用: $0.00 (在免費額度內)
```

---

### 🎯 **總成本估算**

| 項目 | 每月費用 | 說明 |
|------|---------|------|
| Lambda | **$0.00** | ✅ 免費額度內 |
| HTTP API Gateway | **$0.00** | ✅ 免費額度內 |
| ECR | **$0.00** | ✅ 前 12 個月免費 |
| CloudWatch | **$0.00** | ✅ 免費額度內 |
| **Bedrock (Claude)** | **~$0.33** | ⚠️ **唯一收費項目** |
| **總計** | **~$0.33/月** | 約 **NT$ 10/月** |

---

## 🔥 高流量情境（生產環境）

### 假設：每月 100,000 次請求

| 項目 | 費用計算 | 每月費用 |
|------|---------|---------|
| **Lambda 請求** | 100,000 次 (免費額度內) | $0.00 |
| **Lambda 運算** | 200,000 GB-秒 (免費額度內) | $0.00 |
| **HTTP API Gateway** | 100,000 次 (免費額度內) | $0.00 |
| **Bedrock** | 100,000 請求 × $0.000033 | **$3.30** |
| **總計** | | **$3.30/月** |

約 **NT$ 100/月**

---

## 💡 節省成本的建議

### 1. **限制 Bedrock 使用**
- ✅ 設定每日請求上限（例如：100 次/天）
- ✅ 實作請求限流 (Rate Limiting)
- ✅ 使用快取減少重複請求

### 2. **監控使用量**
```python
# 在 api_controller.py 加入請求計數
request_count = 0

@app.route("/v1/company/profile/process", methods=["POST"])
def process_company_profile():
    global request_count
    request_count += 1
    
    # 設定每日上限
    if request_count > 100:
        return jsonify({"error": "每日請求上限已達"}), 429
    # ... 原有邏輯
```

### 3. **使用 CloudWatch 警報**
設定成本警報，當費用超過 $5 時發送通知：
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-cost-alert \
  --alarm-description "Bedrock 成本超過 $5" \
  --metric-name EstimatedCharges \
  --threshold 5.0
```

### 4. **定期清理 ECR 映像**
```bash
# 只保留最新 3 個映像
aws ecr describe-images --repository-name flask-lambda \
  --query 'sort_by(imageDetails,& imagePushedAt)[:-3].[imageDigest]' \
  --output text | xargs -I {} aws ecr batch-delete-image \
  --repository-name flask-lambda --image-ids imageDigest={}
```

---

## ⚠️ 費用警示設定

### 建議設定 AWS Budget

1. **登入 AWS Console**
2. **前往 Billing → Budgets**
3. **建立預算**:
   - 預算類型: Cost budget
   - 金額: $5.00 USD/月
   - 警報閾值: 80% ($4.00)

### 設定 CloudWatch 警報（CLI）
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name monthly-cost-alert \
  --alarm-description "每月成本超過 $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold
```

---

## 🎯 結論

### ✅ **是否會超過免費額度？**

**答案: 不會！**

在**測試/開發階段**（每月 10,000 次請求以內）：
- Lambda、API Gateway、CloudWatch 都在免費額度內
- **唯一費用來自 Bedrock (Claude API)**
- 預估成本: **$0.33/月** (約 NT$ 10)

### 📊 **不同使用量的費用**

| 每月請求數 | Lambda | API Gateway | Bedrock | **總費用** |
|-----------|--------|-------------|---------|-----------|
| 1,000 | $0.00 | $0.00 | $0.03 | **$0.03** (NT$ 1) |
| 10,000 | $0.00 | $0.00 | $0.33 | **$0.33** (NT$ 10) |
| 100,000 | $0.00 | $0.00 | $3.30 | **$3.30** (NT$ 100) |
| 1,000,000 | $0.00 | $0.00 | $33.00 | **$33.00** (NT$ 1000) |

### 🚀 **建議行動**

1. ✅ **可以安心部署到您的私人 AWS**
2. ✅ **設定每日請求上限（例如：100 次）** → 月費 < $1
3. ✅ **啟用 AWS Budget 警報** → 費用超過 $5 通知
4. ✅ **測試完成後刪除資源** → 避免長期費用

---

**報告生成時間**: 2026-04-01
**匯率參考**: 1 USD = 30 TWD (僅供參考)
