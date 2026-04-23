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
        "code": "SUCCESS",  # 統一成功代碼
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


def build_error_response(code, message, details=None, request_id=None):
    response = {
        "success": False,
        "code": code,
        "message": message,
    }
    if details:
        response["details"] = details
    if request_id:
        response["request_id"] = request_id
    return response


def build_server_error_response(message, request_id="req-unknown"):
    return {
        "success": False,
        "code": "INTERNAL_SERVER_ERROR",
        "message": message,
        "request_id": request_id,
    }
