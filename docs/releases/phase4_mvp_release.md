# Phase4 MVP Release (v0.1.0-phase4-mvp)

## 發行摘要
- 版本：v0.1.0-phase4-mvp
- 目的：將 dev-jerry 分支內容上線至 private origin 的 main，包含風控前處理、審核隊列與稽核日誌功能。
- 風險控制：本次為 MVP，已加入基本稽核與回滾指引，建議人工監控首日流量。

## 交付物清單
- 程式碼：主要變更在 dev-jerry 分支（已推送至 origin-private main）
- 程式文件：本檔 release notes
- Tag：v0.1.0-phase4-mvp（已建立並推送至 origin-private）

## 測試結果摘要（簡短）
- 單元測試：關鍵模組通過本地單元測試
- 集成測試：已在開發環境驗證基本流程（審核隊列、稽核日誌寫入）
- 風險：尚未全面負載測試，建議採分階段流量釋放

## 部署指令與檢查
- 部署（已完成於 origin-private main）：
  1. 確認 main 為最新： git fetch origin-private && git checkout main && git reset --hard origin-private/main
  2. 建議在測試環境先執行一次部署流程並檢查日誌

- 回滾指令：
  1. 查詢上一版 tag 或 commit： git tag --sort=-creatordate | head -n 5
  2. 將 main 回到上一個穩定 commit： git checkout main && git reset --hard <COMMIT_HASH> && git push origin-private main --force-with-lease
  3. 注意：force push 會影響 remote，請在有審核同意下操作

- 健康檢查：
  - 檢查稽核日誌： logs/risk_audit.log
  - 檢查審核隊列是否有新增項目： ls data/review_queue | wc -l

## 備註
- 建議下一步建立 GitHub Release 頁面並通知審核與運維人員
