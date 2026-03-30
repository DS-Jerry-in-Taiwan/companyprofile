# Phase 1 Sync MVP - 模組介面設計

## 1. API Controller
- Entry: POST /v1/company/profile/process
- Input: CompanyProfileProcessRequest
- Output: CompanyProfileResponse | ErrorResponse | ServerError

## 2. Request Validator
- 函式: validate_request(payload) -> validated_payload
- 規則:
  - mode in {GENERATE, OPTIMIZE}
  - organNo, organ 必填
  - GENERATE 必填 companyUrl
  - OPTIMIZE 必填 brief
- 失敗: 拋 ValidationError(code=INVALID_REQUEST)

## 3. Core Logic Dispatcher
- 函式: dispatch(mode, validated_payload)
- 邏輯:
  - mode=GENERATE -> GenerateBriefService.run(...)
  - mode=OPTIMIZE -> OptimizeBriefService.run(...)

## 4. Generate Brief Module
- 介面: GenerateBriefService.run(payload) -> DraftContent
- 子模組:
  - WebSearchService.search(organ, companyUrl) -> list[url]
  - WebScraper.extract(urls) -> raw_text
  - TextPreprocessor.normalize(raw_text) -> context_text
  - PromptBuilder.build_generate_prompt(payload, context_text) -> prompt
  - LLMService.generate(prompt) -> LLMOutput

## 5. Optimize Brief Module
- 介面: OptimizeBriefService.run(payload) -> DraftContent
- 子模組:
  - PromptBuilder.build_optimize_prompt(payload) -> prompt
  - LLMService.generate(prompt) -> LLMOutput

## 6. Post-processing Module
- 介面: PostProcessor.process(llm_output) -> SanitizedOutput
- 子模組:
  - HtmlSanitizer.clean(body_html) -> safe_html
  - ContentFilter.filter(summary, tags, body_html) -> filtered_output

## 7. Response Formatter
- 介面: ResponseFormatter.success(payload, sanitized_output) -> CompanyProfileResponse
- 介面: ResponseFormatter.error(code, message, details?) -> ErrorResponse

## 8. Error Handling
- 錯誤類型:
  - ValidationError -> HTTP 400 / INVALID_REQUEST
  - ExternalServiceError -> HTTP 500 / EXTERNAL_SERVICE_ERROR
  - LLMServiceError -> HTTP 500 / LLM_FAILED
  - InternalError -> HTTP 500 / INTERNAL_SERVER_ERROR

## 9. 同步資料流
1. API Controller 接收請求
2. Request Validator 驗證
3. Dispatcher 依 mode 分派
4. Generate/Optimize 執行 LLM
5. Post-processing 處理輸出
6. Response Formatter 回傳結構化結果