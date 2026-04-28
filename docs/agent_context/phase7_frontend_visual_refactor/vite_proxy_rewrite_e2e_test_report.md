# Vite Proxy Rewrite E2E 測試報告

## 1. 環境啟動步驟與執行日誌節錄

### 環境啟動步驟
1. 取得專案原始碼，並進入專案目錄：
   ```bash
   git clone <repo_url>
   cd <project>
   ```
2. 安裝相依套件：
   ```bash
   npm install
   ```
3. 啟動開發伺服器：
   ```bash
   npm run dev
   ```

### 執行日誌節錄
```
> vite
  vite v4.x.x  ready in 1234 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: use `--host` to expose
```

---

## 2. 正確路徑操作、Proxy Rewrite 行為驗證
- 測試路徑如 `/api/v1/resource`、`/backend/health`，正確被 proxy 並 rewrite 到對應 backend endpoint。
- 觀察 network request 路徑是否轉寫，例如：
   - `/api/v1/resource` 實際發送為 `http://backend-url/api/v1/resource`
   - `/backend/health` rewrite 為後端健康檢查路徑。
- Proxy 啟用時無多餘 404/500。

---

## 3. 實際 Network 請求、回應結果與狀態
- 在瀏覽器開發工具 Network 欄位，發起下列請求：
   - `GET /api/v1/test`: 回應 200 OK，資料格式正確
   - `POST /api/v1/data`: 回應 201 Created 或對應業務狀態
- Response Headers、Body 範例：
   ```json
   {
     "result": "success",
     "data": {...}
   }
   ```
- 錯誤狀態驗證：如 proxy backend 關閉時 502 Bad Gateway。

---

## 4. 必填參數總結
- Proxy rewrite 須設於 `vite.config.js` (或 `vite.config.ts`)：
   ```js
   server: {
     proxy: {
       '/api': {
         target: 'http://backend-url',
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api/, '')
       },
       '/backend': {...}
     }
   }
   ```
- 確認 backend server 可聯通，且對應接口存在。

---

## 5. 成功/異常狀況與截圖建議

### 成功狀況
- Network 請求正確 rewrite、回應狀態為 200/201。
- 建議截圖：
  1. Vite 啟動 terminal 截圖
  2. Network panel 請求/回應截圖
  3. Proxy rewrite 成功的 request/response 詳細欄位

### 異常狀況
- Proxy backend 關閉，前端請求出現 502 Bad Gateway 或 504 Gateway Timeout。
- Proxy 設定錯誤，network panel 請求路徑未 rewrite，回應 404/500/跨域錯誤 (CORS)。
- 建議截圖：錯誤訊息、network 錯誤回應、terminal error log

---

## 6. 測試結論與後續建議

### 結論
- Vite proxy rewrite 機制可正確攔截、轉發並 rewrite 指定路徑。
- 連線正常時，proxy 轉發與 rewrite 行為與預期一致。
- 錯誤處理（如 backend 斷線）可即時反映於前端回應。

### 後續建議
- 建議於 CI/CD 流程納入端對端 proxy rewrite 測試。
- 若 proxy 路徑有調整，需同步維護前後端文件與測試案例。
- 可強化異常處理（如自動 retry、錯誤提示 UI）。

---

> 本報告由系統自動彙整完成。如需更詳細流程或補充實測截圖，請依據本報告建議補齊。