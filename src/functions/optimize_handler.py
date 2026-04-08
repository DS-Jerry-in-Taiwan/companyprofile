import json
from utils.llm_handler import BedrockLLMService

# 初始化LLM服務
llm_service = BedrockLLMService()


def handler(event, context):
    """Lambda處理函數，處理公司簡介優化請求"""
    print("Received optimization request")

    try:
        # 解析ALB事件的請求體
        body = json.loads(event.get("body", "{}"))

        # 提取必要參數
        organ_no = body.get("organNo")
        organ = body.get("organ")
        brief = body.get("brief")
        products = body.get("products", "")
        optimization_mode = body.get("optimization_mode", 1)
        trade = body.get("trade")
        word_limit = body.get("word_limit")

        # 驗證必要欄位
        if not brief or not organ_no:
            return _build_error_response(
                400, "INVALID_REQUEST", "公司簡介與公司編號為必填欄位"
            )

        # 呼叫LLM優化服務
        optimized_text = llm_service.optimize_company_brief(
            organ=organ,
            brief=brief,
            products=products,
            optimization_mode=optimization_mode,
            trade=trade,
            word_limit=word_limit,
        )

        # 構建成功回應
        result = {
            "organNo": organ_no,
            "brief": brief,
            "products": products,
            "result": optimized_text,
            "optimization_mode": optimization_mode,
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, ensure_ascii=False),
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return _build_error_response(
            500,
            "INTERNAL_SERVER_ERROR",
            "處理請求時發生錯誤",
            f"req-{hash(str(e)) % 10000000000}",
        )


def _build_error_response(status_code, code, message, request_id=None):
    """構建錯誤回應"""
    error_body = {"code": code, "message": message}

    if request_id:
        error_body["request_id"] = request_id

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(error_body, ensure_ascii=False),
    }
