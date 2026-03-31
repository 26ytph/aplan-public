# ADR-001: 採用 Adapter Pattern 封裝 LLM 呼叫

**日期**：2026-03-09
**狀態**：已接受 (Accepted)

## 背景
專案需要整合 Google Gemini API 進行意圖解析與推薦生成。為了保留未來切換或擴充至 Anthropic Claude 或其他 LLM 的彈性，需要一個抽象化的介面層。

## 決策
採用 **Adapter Pattern (轉接器模式)**，定義 `LLMAdapter` 抽象基類 (ABC)，具體實作為 `GeminiAdapter`。所有 LLM 相關呼叫一律透過 `get_llm_adapter()` 工廠函式取得實體。

## 影響
- `src/utils/llm_adapter.py` 為唯一的 LLM 互動層。
- 任何模型的變更（如從 `gemini-2.5-flash` 切換至 `gemini-3.1-flash-lite-preview`）只需修改此檔案。
- 未來擴充 Claude 僅需新增 `ClaudeAdapter` 子類別。
