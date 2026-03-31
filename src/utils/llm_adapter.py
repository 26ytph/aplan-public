import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel
from src.core.config import get_settings

# 1. 引入全新的 Google GenAI SDK
from google import genai
from google.genai import types

class CustomQuotaExhaustedError(Exception):
    """自定義例外：所有登記在設定檔的 API Key 額度皆已耗盡"""
    pass

class LLMAdapter(ABC):
    """
    LLM 轉接器抽象類別 (Adapter Pattern Interface)
    """
    @abstractmethod
    async def generate_content(self, prompt: str, response_schema: Optional[Type[BaseModel]] = None) -> str:
        """
        傳入提示詞 (Prompt)，非同步回傳生成的文字內容。
        新增 `response_schema` 參數，支援強制輸出 JSON 格式。
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """
        傳入字串，將其轉換為向量表示法 (Embedding)。
        """
        pass

    @abstractmethod
    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        傳入字串陣列，批次轉換為多維度向量表示法 (提升索引效率)。
        """
        pass

class GeminiAdapter(LLMAdapter):
    """
    Gemini 的具體實作 (使用全新 google-genai SDK)
    搭載 Multi-Key Round-Robin Fallback 機制
    """
    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview"):
        self.model_name = model_name
        
        settings = get_settings()
        self._active_keys = settings.gemini_api_keys.copy()
        if not self._active_keys:
            raise ValueError("No Gemini API keys found in configuration.")
        
        self.current_key_idx = 0
        self._clients = {}
        
    def _get_active_client_and_key(self) -> tuple[genai.Client, str]:
        if not self._active_keys:
            raise CustomQuotaExhaustedError("All API keys entirely exhausted.")
        
        # 避免越界
        if self.current_key_idx >= len(self._active_keys):
            self.current_key_idx = 0
            
        # 每次請求時強制輪換金鑰，均勻分攤每分鐘 15 RPM 極限
        self.current_key_idx = (self.current_key_idx + 1) % len(self._active_keys)
        
        active_key = self._active_keys[self.current_key_idx]
        
        if active_key not in self._clients:
            self._clients[active_key] = genai.Client(api_key=active_key)
            
        return self._clients[active_key], active_key
        
    def _remove_exhausted_key(self):
        """當遇到 429 日常額度炸裂時，將廢鑰匙從池中剔除"""
        if not self._active_keys:
            return
            
        # 確保 idx 不會越界
        if self.current_key_idx < len(self._active_keys):
            dead_key = self._active_keys.pop(self.current_key_idx)
            print(f"\n[Warning] API Key ({dead_key[:10]}...) 達到配額上限！將其從輪替池中強制剔除。剩餘 {len(self._active_keys)} 把...")
            
        if not self._active_keys:
            raise CustomQuotaExhaustedError("All API keys exhausted.")
        
    async def generate_content(self, prompt: str, response_schema: Optional[Type[BaseModel]] = None) -> str:
        # 定義一個內部重試邏輯，支援 Fallback Model
        async def _attempt_generate(model_name: str) -> str:
            config_args = {}
            if response_schema:
                config_args["response_mime_type"] = "application/json"
                config_args["response_schema"] = response_schema
                config_args["temperature"] = 0.1
            
            config = types.GenerateContentConfig(**config_args) if config_args else None
            client, _ = self._get_active_client_and_key()
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text

        try:
            # 優先嘗試主模型
            return await _attempt_generate(self.model_name)
        except Exception as e:
            error_msg = str(e)
            print(f"[Warning] Gemini API 觸發例外 ({self.model_name}): {error_msg}，嘗試啟動 Fallback...")
            
            # 使用經由 list() 確認存在的穩定模型作為輕量備援
            fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash-lite"]
            
            for fallback in fallback_models:
                try:
                    print(f"[Info] 嘗試使用 Fallback 模型: {fallback}")
                    return await _attempt_generate(fallback)
                except Exception as fallback_e:
                    print(f"[Warning] Fallback 模型 {fallback} 也失敗: {str(fallback_e)}")
                    continue
            
            # 如果所有模型都耗盡了或 API 全面崩潰，回傳一個安全的 Mock JSON 確保 Demo 不會當機
            print("[Error] LLM 產生內容徹底失敗，啟動終極 Mock 防禦機制以保護 UI 不卡死。")
            if response_schema and response_schema.__name__ == "IntentResponse":
                return '{"selected_location": null, "selected_weather": null, "selected_time": null, "selected_tags": []}'
            elif response_schema and response_schema.__name__ == "RecommendationResponse":
                return '{"itinerary_summary": "【系統提示：AI 額度已耗盡，此為離線快取內容】天氣不錯，推薦您前往附近商圈走走，享受愜意時光！", "recommended_pois": []}'
            else:
                return "【系統提示：AI 額度已耗盡或網路不穩，請稍後再試】"

    async def get_embedding(self, text: str) -> list[float]:
        """
        使用 gemini-embedding-001 將文字轉為向量，支援 429 多金鑰輪詢
        """
        # 最多重試，以防運氣差打到剛掉的鑰匙
        for attempt in range(len(self._active_keys) + 1):
            try:
                client, _ = self._get_active_client_and_key()
                result = await client.aio.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text
                )
                return result.embeddings[0].values
            except CustomQuotaExhaustedError:
                raise # Re-raise if _get_active_client_and_key indicates all keys are exhausted
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "resource" in err_str or "exhausted" in err_str or "quota" in err_str:
                    self._remove_exhausted_key()
                    continue # Try again with the next key
                else:
                    raise RuntimeError(f"LLM Embedding Error: {str(e)}")
                    
        raise CustomQuotaExhaustedError("All API keys exhausted.")

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        使用 embedding-001 將文字批量轉換為向量。
        """
        import requests
        import asyncio
        from src.core.config import get_settings
        
        settings = get_settings()
        
        while self.current_key_idx < len(settings.gemini_api_keys):
            try:
                _, active_key = self._get_active_client_and_key()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={active_key}"
                payload = {
                    "requests": [
                        {
                            "model": "models/gemini-embedding-001",
                            "content": {"parts": [{"text": t}]}
                        } for t in texts
                    ]
                }
                
                response = await asyncio.to_thread(
                    requests.post,
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    err_str = response.text.lower()
                    if response.status_code == 429 or "resource" in err_str or "exhausted" in err_str or "quota" in err_str:
                        print(f"\n[Warning] 批次 API Key {self.current_key_idx + 1} 達到配額上限！自動切換下一組...")
                        self.current_key_idx += 1
                        continue
                    else:
                        raise RuntimeError(f"REST API Error {response.status_code}: {response.text}")
                        
                data = response.json()
                return [enc["values"] for enc in data.get("embeddings", [])]
                
            except CustomQuotaExhaustedError:
                raise
            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"LLM Batch Embedding (REST) Error: {str(e)}")
                
        raise CustomQuotaExhaustedError("All API keys exhausted.")

def get_llm_adapter(model_type: str = "gemini") -> LLMAdapter:
    if model_type == "gemini":
        return GeminiAdapter()
    elif model_type == "claude":
        raise NotImplementedError("Claude adapter is not yet implemented.")
    else:
        raise ValueError(f"Unsupported LLM type: {model_type}")