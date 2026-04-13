# Dockerfile - 通用 Lambda 映像
# 適用於開發、測試和生產環境
# 通過 build args 和環境變數區分環境

FROM public.ecr.aws/lambda/python:3.11

# 設置工作目錄（Lambda 標準工作目錄）
WORKDIR ${LAMBDA_TASK_ROOT}

# 設置環境變數
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 複製依賴檔案
COPY src/functions/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY src/functions/lambda_handler.py .
COPY src/functions/api_controller.py .
COPY src/functions/utils/ ./utils/
COPY src/ ./src/

# 複製模板文件（LLM 服務需要）
COPY src/functions/generate_prompt_template.txt .
COPY src/functions/optimize_prompt_template.txt .

# 創建數據目錄並複製詞庫文件
RUN mkdir -p ./data
COPY src/plugins/taiwan_terms/data/terms.json ./data/terms.json
RUN chmod 644 ./data/terms.json

# 設置環境變數（可通過 build args 覆寫）
ARG STAGE=dev
ARG VERSION=unknown
ARG BUILD_DATE=unknown
ENV STAGE=${STAGE}
ENV VERSION=${VERSION}
ENV BUILD_DATE=${BUILD_DATE}

# 設置 Lambda 處理函數入口點
CMD ["lambda_handler.handler"]