import json
import boto3
import os

class BedrockLLMService:
    """與Amazon Bedrock模型互動的服務類"""
    
    def __init__(self):
        """初始化Bedrock服務"""
        bedrock_region = os.environ.get('BEDROCK_REGION', 'ap-northeast-1')
        self.model_id = os.environ.get('CLAUDE_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
        
        # 初始化Bedrock客戶端
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=bedrock_region)
    
    def optimize_company_brief(self, organ, brief, products="", optimization_mode=1, trade=None, word_limit=None):
        """使用Bedrock Claude優化公司簡介"""
        # 構建提示詞
        prompt = self._build_optimization_prompt(organ, brief, products, optimization_mode, trade, word_limit)
        
        try:
            # 調用Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                })
            )
            
            # 解析回應
            response_body = json.loads(response['body'].read())
            optimized_text = response_body['content'][0]['text']
            
            return optimized_text
            
        except Exception as e:
            print(f"Error calling Bedrock: {str(e)}")
            raise Exception(f"LLM服務調用失敗: {str(e)}")
    
    def _build_optimization_prompt(self, organ, brief, products, mode, trade=None, word_limit=None):
        """構建優化提示詞"""
        mode_descriptions = {
            1: "標準模式：平衡簡潔與詳細度的一般優化",
            2: "簡潔模式：生成更精簡的公司描述",
            3: "詳細模式：生成更詳盡的公司描述"
        }
        
        prompt = f"""
                你是一位專業的企業文案優化專家，擅長改寫企業描述使其更專業、更有吸引力。
                根據你對這間公司的認識，幫我優化以下公司簡介，遵循以下要求：
                1. 公司名稱: {organ}
                2. 優化模式: {mode_descriptions.get(mode, mode_descriptions[1])}
                3. 產品/服務: {products}
                """
                        
        if trade:
            prompt += f"4. 產業類型代碼: {trade}\n"
        
        if word_limit:
            prompt += f"5. 字數限制: 不超過{word_limit}字\n"
        
        prompt += f"""
                請保留原文中的關鍵信息，同時使文字更流暢、更有商業專業感。
                如果原文中有明顯的排版如<br>標籤，請在輸出中保留。

                原始公司描述:
                {brief}

                優化後的公司描述:
                """
        
        return prompt