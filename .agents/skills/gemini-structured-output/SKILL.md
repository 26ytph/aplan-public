---
name: gemini-structured-output
description: 如何正確使用 Google GenAI SDK 的 response_schema 參數搭配 Pydantic Model 實現強制 JSON 結構化輸出
---

# Gemini Structured Output (強制 JSON 輸出) Skill

## 適用場景
當你需要 Gemini LLM 回傳**嚴格符合 Pydantic Schema 的 JSON**，而非自由文字時。

## 核心用法

### 1. 定義 Pydantic Model
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class IntentResponse(BaseModel):
    selected_location: Optional[str] = Field(None)
    selected_weather: Optional[str] = Field(None)
    selected_tags: List[str] = Field(default_factory=list)
```

### 2. 傳入 `response_schema` 參數
```python
from google.genai import types

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=IntentResponse,  # 直接傳入 Pydantic class
    temperature=0.1
)

response = await client.aio.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents=prompt,
    config=config
)
```

## 已驗證支援 Structured Output 的模型清單 (2026-03)

| 模型名稱 | 支援 response_schema | Free Tier RPD |
|----------|---------------------|---------------|
| `gemini-3.1-flash-lite-preview` | ✅ | 1,500 |
| `gemini-2.5-flash` | ✅ | ~50 (低) |
| `gemini-2.0-flash` | ✅ | 較高 |
| `gemini-2.5-flash-lite` | ✅ | 較高 |
| `gemini-3-flash-preview` | ❌ 404 NOT_FOUND | N/A |
| `gemini-1.5-flash` | ❌ 不在新版 SDK 清單 | N/A |

## ⚠️ 踩坑紀錄

1. **模型名稱必須精確**：`gemini-3-flash-preview` 和 `gemini-3.1-flash-lite-preview` 差一個 `.1` 和 `-lite`，前者會回傳 `404 NOT_FOUND`。
2. **驗證可用模型**：用以下腳本確認帳號下可用的模型：
   ```python
   from google import genai
   client = genai.Client(api_key="YOUR_KEY")
   for m in client.models.list():
       print(m.name)
   ```
3. **Pydantic Model 必須唯一定義**：不要在多個檔案中定義同名 Model，否則 `response_schema` 可能指向錯誤的版本。統一放在 `schemas.py`。
