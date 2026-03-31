---
name: sqlite-to-excel-export
description: 將 SQLite 資料庫的資料依分類匯出成 Excel 多分頁格式（.xlsx），適合資料盤點、對外分享或人工審查
---

# SQLite → Excel 多分頁匯出 Skill

## 適用場景
- 想把 SQLite 資料按 `source` 或 `category` 欄位分類後，各自放進不同的 Excel Sheet
- 需要給非技術人員一份可以直接用 Google Sheets / Excel 開啟的資料清單
- 需要定期產出資料快照存檔

## 前置需求
```bash
.venv/bin/pip install pandas openpyxl
```
（執行前先確認 `.venv` 環境中已安裝）

## 步驟流程

### 1. 先查詢分類與筆數（讓 AI 跟使用者確認）

AI 應先執行以下 SQL，列出分類名稱與筆數，**等待使用者確認後才開始匯出**：

```python
import sqlite3
conn = sqlite3.connect('test.db')
cur = conn.cursor()

# 查看 source 分布
cur.execute('SELECT source, COUNT(*) FROM pois GROUP BY source ORDER BY COUNT(*) DESC')
for row in cur.fetchall():
    print(row)

# 查看 category 分布（依不同 source）
cur.execute('SELECT source, category, COUNT(*) FROM pois GROUP BY source, category ORDER BY source, COUNT(*) DESC')
for row in cur.fetchall():
    print(row)

conn.close()
```

### 2. 確認分頁規劃後，執行匯出腳本

```python
import sqlite3, pandas as pd
from datetime import datetime

conn = sqlite3.connect('test.db')
today = datetime.now().strftime('%Y%m%d')
output_file = f'data_export_{today}.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

    # ---- TDX 來源：依 category 分頁 ----
    for cat, sheet_name in [('spot', 'TDX_景點'), ('food', 'TDX_餐廳美食'), ('hotel', 'TDX_旅館住宿'), ('event', 'TDX_活動展覽')]:
        df = pd.read_sql_query(
            f"SELECT * FROM pois WHERE source='TDX_API' AND category='{cat}' ORDER BY id",
            conn
        )
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f'{sheet_name}: {len(df)} 筆')

    # ---- OSM 來源：合併成一個 Sheet（source 欄位區分行政區）----
    df = pd.read_sql_query(
        "SELECT * FROM pois WHERE source LIKE 'OSM%' ORDER BY source, id",
        conn
    )
    df.to_excel(writer, sheet_name='OSM_全部', index=False)
    print(f'OSM_全部: {len(df)} 筆')

conn.close()
print(f'✅ 匯出完成: {output_file}')
```

> 💡 **彈性提示**：Sheet 分頁的規劃可依使用者需求調整。  
> 例如：若 OSM 要拆成每個行政區一個 Sheet，只要改為依 `source` 欄位 group_by 並分別輸出即可。

## 注意事項
1. **Excel 單一 Sheet 上限** 為 1,048,576 列，大量 OSM 資料（13,000+ 筆）放在一個 Sheet 完全沒問題。
2. 匯出檔名格式為 `data_export_YYYYMMDD.xlsx`，預設存放在執行目錄（通常是專案根目錄）。
3. 若資料欄位中有 `None` 或中文特殊字元，`pandas` 會自動處理，無需額外 escape。

## 呼叫語法範例

```
/sqlite-to-excel-export 請把 SQLite 中的所有 POI 資料，依 source 分類匯出成 Excel，
OSM 的部分合併成一個 Sheet，TDX 的部分依 category 分成不同 Sheet。
```

或更精簡的呼叫：
```
/sqlite-to-excel-export 先列出分類與筆數，待我確認後匯出 Excel。
```
