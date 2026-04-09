# 🔧 快速修正指南 - 找到正確位置了！

**找到位置**: `src/functions/utils/response_formatter.py`  
**函數**: `build_success_response` (第4-15行)  
**狀態**: 需要修改這裡！

---

## 🎯 正確的修改位置

### 檔案
```
/src/functions/utils/response_formatter.py
```

### 當前代碼 (第4-15行)
```python
def build_success_response(payload, generated):
    return {
        "success": True,
        "organNo": payload.get("organNo"),
        "organ": payload.get("organ"),
        "mode": payload.get("mode"),
        "title": generated.get("title", ""),
        "body_html": generated.get("body_html", ""),  # ← 這裡
        "summary": generated.get("summary", ""),
        "tags": generated.get("tags", []),
        "risk_alerts": generated.get("risk_alerts", []),
    }
```

---

## ✏️ 需要做的修改

### 步驟 1: 添加 HTML 解析函數

在檔案頂部添加：

```python
"""HTTP response payload builders for success/error models."""

from html.parser import HTMLParser

class ContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.links = []
        self.current_para = []
        self.in_link = False
        self.current_link = {}
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.in_link = True
            attrs_dict = dict(attrs)
            self.current_link = {'url': attrs_dict.get('href', '')}
            
    def handle_data(self, data):
        if self.in_link:
            self.current_link['text'] = data.strip()
        else:
            self.current_para.append(data)
            
    def handle_endtag(self, tag):
        if tag == 'p':
            para_text = ''.join(self.current_para).strip()
            if para_text:
                self.paragraphs.append(para_text)
            self.current_para = []
        elif tag == 'a':
            if self.current_link:
                self.links.append(self.current_link)
            self.in_link = False
            self.current_link = {}

def extract_content_from_html(html_content):
    """從 HTML 中提取段落和連結"""
    if not html_content:
        return {"paragraphs": [], "links": [], "plain": ""}
    
    extractor = ContentExtractor()
    extractor.feed(html_content)
    
    return {
        "paragraphs": extractor.paragraphs,
        "links": extractor.links,
        "plain": '\n\n'.join(extractor.paragraphs)
    }
```

### 步驟 2: 修改 build_success_response 函數

```python
def build_success_response(payload, generated):
    # 從 body_html 提取內容
    body_html = generated.get("body_html", "")
    extracted = extract_content_from_html(body_html)
    
    return {
        "success": True,
        "organNo": payload.get("organNo"),
        "organ": payload.get("organ"),
        "mode": payload.get("mode"),
        "title": generated.get("title", ""),
        
        # 原有欄位 (保持兼容)
        "body_html": body_html,
        "summary": generated.get("summary", ""),
        "tags": generated.get("tags", []),
        "risk_alerts": generated.get("risk_alerts", []),
        
        # 🆕 新增欄位
        "content_paragraphs": extracted["paragraphs"],
        "content_links": extracted["links"],
        "content_plain": extracted["plain"],
    }
```

---

## ✅ 修改後的完整檔案

```python
"""HTTP response payload builders for success/error models."""

from html.parser import HTMLParser


class ContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.links = []
        self.current_para = []
        self.in_link = False
        self.current_link = {}
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.in_link = True
            attrs_dict = dict(attrs)
            self.current_link = {'url': attrs_dict.get('href', '')}
            
    def handle_data(self, data):
        if self.in_link:
            self.current_link['text'] = data.strip()
        else:
            self.current_para.append(data)
            
    def handle_endtag(self, tag):
        if tag == 'p':
            para_text = ''.join(self.current_para).strip()
            if para_text:
                self.paragraphs.append(para_text)
            self.current_para = []
        elif tag == 'a':
            if self.current_link:
                self.links.append(self.current_link)
            self.in_link = False
            self.current_link = {}


def extract_content_from_html(html_content):
    """從 HTML 中提取段落和連結"""
    if not html_content:
        return {"paragraphs": [], "links": [], "plain": ""}
    
    extractor = ContentExtractor()
    extractor.feed(html_content)
    
    return {
        "paragraphs": extractor.paragraphs,
        "links": extractor.links,
        "plain": '\n\n'.join(extractor.paragraphs)
    }


def build_success_response(payload, generated):
    # 從 body_html 提取內容
    body_html = generated.get("body_html", "")
    extracted = extract_content_from_html(body_html)
    
    return {
        "success": True,
        "organNo": payload.get("organNo"),
        "organ": payload.get("organ"),
        "mode": payload.get("mode"),
        "title": generated.get("title", ""),
        "body_html": body_html,
        "summary": generated.get("summary", ""),
        "tags": generated.get("tags", []),
        "risk_alerts": generated.get("risk_alerts", []),
        "content_paragraphs": extracted["paragraphs"],
        "content_links": extracted["links"],
        "content_plain": extracted["plain"],
    }


def build_error_response(code, message, details=None):
    response = {
        "success": False,
        "code": code,
        "message": message,
    }
    if details:
        response["details"] = details
    return response


def build_server_error_response(message, request_id="req-unknown"):
    return {
        "success": False,
        "code": "INTERNAL_SERVER_ERROR",
        "message": message,
        "request_id": request_id,
    }
```

---

## 🚀 修改步驟

### 1. 打開檔案
```bash
vim /src/functions/utils/response_formatter.py
# 或
nano /src/functions/utils/response_formatter.py
# 或
code /src/functions/utils/response_formatter.py
```

### 2. 複製上方"修改後的完整檔案"內容

### 3. 保存檔案
```
Ctrl+S (或 :wq in vim)
```

### 4. 重啟後端服務
```bash
Ctrl+C  # 停止當前服務
python app.py  # 重新啟動
```

### 5. 驗證修改
運行測試腳本，檢查新欄位是否出現。

---

## ✅ 完成後的 API 回應示例

```json
{
  "success": true,
  "organNo": "117164920",
  "organ": "澳霸有限公司",
  "mode": "GENERATE",
  "title": "澳霸有限公司 - 專業服務",
  "body_html": "<p>澳霸有限公司成立於2000年...</p><p>...</p>",
  "summary": "澳霸有限公司秉持永續經營理念...",
  "tags": ["環保建材", "藝術塗料"],
  "risk_alerts": [],
  "content_paragraphs": [
    "澳霸有限公司成立於2000年，總部設於...",
    "澳霸有限公司秉持永續經營的理念..."
  ],
  "content_links": [
    {
      "text": "https://twincn.com/item.aspx?no=42965130",
      "url": "https://twincn.com/item.aspx?no=42965130"
    }
  ],
  "content_plain": "澳霸有限公司成立於2000年...\n\n澳霸有限公司秉持永續經營的理念..."
}
```

---

## 🎯 預計時間

- 修改代碼: 5分鐘
- 重啟服務: 10秒
- 驗證測試: 30秒

**總計: 約 6 分鐘**

---

**修改完成後通知我，立即運行 Checkpoint 1 完整測試！** 🧪
