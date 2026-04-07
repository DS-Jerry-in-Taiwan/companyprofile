"""HTTP response payload builders for success/error models."""


def build_success_response(payload, generated):
    return {
        "success": True,
        "organNo": payload.get("organNo"),
        "organ": payload.get("organ"),
        "mode": payload.get("mode"),
        "title": generated.get("title", ""),
        "body_html": generated.get("body_html", ""),
        "summary": generated.get("summary", ""),
        "tags": generated.get("tags", []),
        "risk_alerts": generated.get("risk_alerts", []),
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
