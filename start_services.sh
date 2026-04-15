#!/bin/bash
# 啟動 OrganBriefOptimization 服務

echo "啟動 OrganBriefOptimization 服務..."
echo "日期: $(date)"

# 啟動後端 Flask 服務
echo "啟動後端 Flask 服務..."
cd /home/ubuntu/projects/OrganBriefOptimization/src/functions
nohup python api_controller.py > /tmp/flask_backend.log 2>&1 &
FLASK_PID=$!
echo "Flask 進程 PID: $FLASK_PID"

# 等待 Flask 啟動
sleep 3

# 檢查 Flask 是否運行
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask 服務已啟動 (PID: $FLASK_PID)"
else
    echo "❌ Flask 服務啟動失敗"
    echo "檢查日誌: /tmp/flask_backend.log"
fi

# 啟動前端 Vite 服務
echo "啟動前端 Vite 服務..."
cd /home/ubuntu/projects/OrganBriefOptimization/frontend
nohup npm run dev > /tmp/vite_frontend.log 2>&1 &
VITE_PID=$!
echo "Vite 進程 PID: $VITE_PID"

# 等待 Vite 啟動
sleep 3

# 檢查 Vite 是否運行
if ps -p $VITE_PID > /dev/null; then
    echo "✅ Vite 服務已啟動 (PID: $VITE_PID)"
else
    echo "❌ Vite 服務啟動失敗"
    echo "檢查日誌: /tmp/vite_frontend.log"
fi

echo ""
echo "服務狀態:"
echo "後端 API: http://localhost:5000/v1/company/profile/process"
echo "前端界面: http://localhost:5173"
echo ""
echo "測試 API:"
echo "curl -X POST http://localhost:5000/v1/company/profile/process \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"organNo\": \"TEST001\", \"organ\": \"Google\", \"mode\": \"GENERATE\", \"template\": \"CONCISE\"}'"
echo ""
echo "日誌文件:"
echo "- Flask: /tmp/flask_backend.log"
echo "- Vite: /tmp/vite_frontend.log"
echo ""
echo "按 Ctrl+C 停止服務"