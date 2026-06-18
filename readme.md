# 三國志 禮包兌換碼 CLI 工具

一鍵批量兌換禮包碼的命令行工具，支援多帳號批次處理。

## 功能特色

- 🎁 快速兌換禮包碼
- 👥 支援多帳號批次兌換
- 🌏 支援 Unicode / 中文兌換碼
- 📊 顯示詳細兌換結果
- 🤖 **監控模式**：自動監聽 LINE 聊天訊息，偵測到兌換碼時自動兌換

## 安裝

### 使用 uv（推薦）

```bash
# 安裝 uv（如果尚未安裝）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依賴
uv sync
```

### 使用 pip（替代方案）

```bash
pip install requests flask line-bot-sdk
```

## 設定

### 1. 設定玩家資料

編輯 `hkusers.json` 檔案，填入你的遊戲資料：

```json
[
    {
        "player_id": "你的角色編號",
        "player_name": "你的角色名稱"
    }
]
```

#### 多帳號設定

如果有多個帳號，可以加入多筆資料：

```json
[
    {
        "player_id": "123456",
        "player_name": "玩家A"
    },
    {
        "player_id": "789012",
        "player_name": "玩家B"
    }
]
```

> ⚠️ **注意**：角色名稱需與遊戲內完全一致，包含特殊字符（如 `丨` 不等於 `|`）

### 2. 設定 LINE Bot（僅監控模式需要）

#### 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立新的 Provider 和 Channel
3. 取得 **Channel Secret** 和 **Channel Access Token**

#### 設定方式（擇一）

**方式 A：使用設定檔（推薦）**

複製範例設定檔並填入你的資訊：

```bash
cp line_config.json.example line_config.json
```

編輯 `line_config.json`：

```json
{
  "channel_secret": "你的_CHANNEL_SECRET",
  "channel_access_token": "你的_CHANNEL_ACCESS_TOKEN",
  "target_group_id": null,
  "pattern": "[\\w\\u4e00-\\u9fff]{4,20}"
}
```

- `target_group_id`: 如果設為 `null`，會監聽所有聊天；設為特定群組 ID 則只監聽該群組
- `pattern`: 兌換碼的匹配規則（正則表達式），預設為 4-20 個英數字或中文字

**方式 B：使用環境變數**

```bash
export LINE_CHANNEL_SECRET="你的_CHANNEL_SECRET"
export LINE_CHANNEL_ACCESS_TOKEN="你的_CHANNEL_ACCESS_TOKEN"
export LINE_TARGET_GROUP_ID="群組ID"  # 選填
export REDEMPTION_PATTERN="[\\w\\u4e00-\\u9fff]{4,20}"  # 選填
```

#### 設定 Webhook URL

1. 在 LINE Developers Console 中，設定 Webhook URL 為：`https://你的網域/callback`
2. 啟用 Webhook
3. 如果使用本地測試，可以使用 [ngrok](https://ngrok.com/) 等工具建立隧道：
   ```bash
   ngrok http 5000
   ```
   然後將 ngrok 提供的 URL 設定為 Webhook URL

## 使用方法

### 模式一：手動兌換（CLI 模式）

```bash
# 為所有帳號兌換
uv run main.py --code "ABC123XYZ"

# 支援中文兌換碼
uv run main.py --code "新年快樂2024"

# 只為特定帳號兌換（使用索引，從 0 開始）
uv run main.py --code "ABC123XYZ" --user-index 0
```

> 💡 也可以使用 `python main.py` 如果已經安裝依賴

### 模式二：監控模式（自動兌換）

啟動監控伺服器，自動監聽 LINE 聊天訊息：

```bash
# 使用預設埠號 5000
uv run main.py --monitor

# 使用自訂埠號
uv run main.py --monitor --port 8080
```

**運作方式：**

1. 伺服器啟動後會監聽 LINE Webhook 事件
2. 當 LINE 聊天中出現符合模式的文字時（預設：4-20 個英數字或中文字）
3. 自動提取兌換碼並為所有帳號進行兌換
4. 在 LINE 聊天中回覆兌換結果

**範例：**

當有人在 LINE 群組中發送：
```
今天有新的兌換碼：ABC123XYZ
```

系統會自動：
1. 偵測到 `ABC123XYZ` 符合兌換碼模式
2. 為所有 `hkusers.json` 中的帳號進行兌換
3. 在群組中回覆結果：
   ```
   🎁 兌換碼: ABC123XYZ
   📊 結果: 10 成功, 0 失敗
   
   ✅ 喵寶丨銀子: 禮包獎勵: 金幣x1000
   ✅ 鬼丨初始: 禮包獎勵: 金幣x1000
   ...
   ```

### 參數說明

#### CLI 模式參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `--code` | ✅ | 禮包兌換碼（CLI 模式必填） |
| `--user-index` | ❌ | 指定 users.json 中的帳號索引（預設：兌換所有帳號）|

#### 監控模式參數

| 參數 | 必填 | 說明 |
|------|------|------|
| `--monitor` | ✅ | 啟動監控模式 |
| `--port` | ❌ | Webhook 伺服器埠號（預設：5000）|

### 查看幫助

```bash
uv run main.py --help
```

## 輸出範例

### 成功兌換

```
🎁 Redeeming code: ABC123XYZ
👥 Processing 1 user(s)
==================================================

📤 User: 喵寶丨銀子 (ID: 658957)
   Status: 200
   Response: {
     "code": 200,
     "items": [...]
   }
   ✅ Success! 禮包獎勵: 金幣x1000, 元寶x50

==================================================
📊 Results: 1 success, 0 failed
```

### 兌換失敗

```
🎁 Redeeming code: INVALID_CODE
👥 Processing 1 user(s)
==================================================

📤 User: 喵寶丨銀子 (ID: 658957)
   Status: 200
   Response: {
     "code": 419,
     "message": "active code unusable"
   }
   ❌ Failed: active code unusable

==================================================
📊 Results: 0 success, 1 failed
```

## 常見錯誤訊息

| 錯誤訊息 | 說明 |
|----------|------|
| `active code unusable` | 兌換碼不存在或已達兌換上限 |
| `code has been used` | 此帳號已兌換過此碼 |
| `player not found` | 角色編號或名稱錯誤 |

## 相關連結

- 官方兌換頁面：https://game-notice.qookkagames.com/64103079d26d1f0ace5fb304/index

## License

MIT

