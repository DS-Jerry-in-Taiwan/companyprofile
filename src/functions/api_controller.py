# api_controller.py
"""
API Gateway / Controller
- Flask 實作，單一端點 POST /v1/company/profile/process
"""
import uuid
from flask import Flask, request, jsonify
from utils.request_validator import validate_request, ValidationError
from utils.core_dispatcher import dispatch_core_logic
from utils.error_handler import ExternalServiceError, LLMServiceError
from utils.response_formatter import (
    build_success_response,
    build_error_response,
    build_server_error_response,
)

app = Flask(__name__)

@app.route('/v1/company/profile/process', methods=['POST'])
def process_company_profile():
    try:
        data = request.get_json(force=True)
        valid_data = validate_request(data)
        result = dispatch_core_logic(valid_data)
        return jsonify(build_success_response(valid_data, result))
    except ValidationError as ve:
        return jsonify(build_error_response(ve.code, ve.message, ve.details)), 400
    except (ExternalServiceError, LLMServiceError) as se:
        return jsonify(build_server_error_response(se.message, request_id=f'req-{uuid.uuid4().hex[:8]}')), 500
    except Exception:
        return jsonify(build_server_error_response('unexpected internal error', request_id=f'req-{uuid.uuid4().hex[:8]}')), 500

if __name__ == '__main__':
    app.run(debug=True)
