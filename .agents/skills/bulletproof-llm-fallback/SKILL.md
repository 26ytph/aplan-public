---
name: bulletproof-llm-fallback
description: 通用的 LLM 多模型容錯降級模板，確保 AI 應用在任何極端情境下都不當機
---

# Bulletproof LLM Fallback (不死鳥防護網) Skill

## 適用場景
當你的應用依賴外部 LLM API，且必須在以下情境中存活：
- API Rate Limit (HTTP 429)
- 模型不存在 (HTTP 404)
- 網路斷線 / Timeout
- 免費額度耗盡

## 核心設計原則

### 1. 無差別 `try-except`（捕捉所有例外）
**絕對不要**只攔截特定的 HTTP 錯誤碼。黑客松現場什麼鬼都會發生。

```python
try:
    return await _attempt_generate(self.model_name)
except Exception as e:
    # 無論什麼錯，都進入 Fallback 流程
    print(f"[Warning] 主模型失敗: {e}")
```

### 2. 分級降階 Fallback 模型清單
```python
fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash-lite"]

for fallback in fallback_models:
    try:
        return await _attempt_generate(fallback)
    except Exception:
        continue
```

### 3. 終極 Mock JSON 防線
當所有模型都失敗時，回傳一個**能讓前端正常渲染的靜態 JSON**：

```python
if response_schema and response_schema.__name__ == "IntentResponse":
    return '{"selected_location": null, "selected_weather": null, "selected_time": null, "selected_tags": []}'
elif response_schema and response_schema.__name__ == "RecommendationResponse":
    return '{"itinerary_summary": "【系統提示：AI 暫時離線】", "recommended_pois": []}'
```

## 關鍵要點
- Mock JSON 的結構**必須完全符合**前端期望的 Pydantic Schema，否則會觸發 422 Validation Error。
- 透過 `response_schema.__name__` 辨別不同的 API Endpoint，回傳對應的 Mock 結構。
- 前端收到 Mock 時應以 Toast 通知使用者「目前為離線模式」，而非靜默忽略。
