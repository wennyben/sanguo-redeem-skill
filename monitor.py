#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Bot webhook server for Sanguo code redemption.
Only responds to @mentions in group chats.
"""

import json
import os
import re
import sys
from flask import Flask, request, abort

from redeem import process_redemption

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────────────

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
TARGET_GROUP_ID = os.environ.get("LINE_TARGET_GROUP_ID", None)  # None = all groups

# Default pattern: 4-20 alphanumeric/Chinese characters
REDEMPTION_PATTERN = os.environ.get(
    "REDEMPTION_PATTERN", r"[\w\u4e00-\u9fff]{4,20}"
)

# Try loading from config file if env vars are not set
_config_path = os.path.join(os.path.dirname(__file__), "line_config.json")
if os.path.exists(_config_path) and (not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN):
    with open(_config_path, "r", encoding="utf-8") as f:
        _cfg = json.load(f)
    CHANNEL_SECRET = CHANNEL_SECRET or _cfg.get("channel_secret", "")
    CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN or _cfg.get("channel_access_token", "")
    TARGET_GROUP_ID = TARGET_GROUP_ID or _cfg.get("target_group_id", None)
    REDEMPTION_PATTERN = REDEMPTION_PATTERN or _cfg.get(
        "pattern", r"[\w\u4e00-\u9fff]{4,20}"
    )

# ── LINE Bot helpers ────────────────────────────────────────────────────

def reply_message(reply_token: str, messages: list):
    """Send a reply message via LINE Messaging API."""
    import requests

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    body = {
        "replyToken": reply_token,
        "messages": messages,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=10)
    if resp.status_code != 200:
        print(f"[LINE] reply failed: {resp.status_code} {resp.text}", file=sys.stderr)


def push_message(group_id: str, messages: list):
    """Send a push message to a group (no replyToken needed)."""
    import requests

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    body = {
        "to": group_id,
        "messages": messages,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=10)
    if resp.status_code != 200:
        print(f"[LINE] push failed: {resp.status_code} {resp.text}", file=sys.stderr)


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook signature."""
    import base64
    import hashlib
    import hmac

    if not CHANNEL_SECRET:
        return True  # skip verification if no secret configured

    hash_val = hmac.new(
        CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(hash_val).decode("utf-8")
    return hmac.compare_digest(expected, signature)


# ── Code extraction ─────────────────────────────────────────────────────

def extract_code(text: str) -> str | None:
    """Extract a redemption code from message text."""
    # Remove @mention prefixes (e.g. "@BotName ")
    text = re.sub(r"@\S+\s*", "", text).strip()
    match = re.search(REDEMPTION_PATTERN, text)
    return match.group(0) if match else None


# ── User loading ────────────────────────────────────────────────────────

def load_users():
    """Load user data from user.json."""
    users_file = os.environ.get(
        "SANGUO_USERS_FILE",
        os.path.join(os.path.dirname(__file__), "user.json"),
    )
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] {users_file} not found", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {users_file}: {e}", file=sys.stderr)
        return []


# ── Webhook handler ─────────────────────────────────────────────────────

@app.route("/callback", methods=["POST"])
def callback():
    # Verify signature
    signature = request.headers.get("X-Line-Signature", "")
    body_bytes = request.get_data()
    if not verify_signature(body_bytes, signature):
        abort(400)

    body = request.get_json()
    if not body:
        return "OK"

    for event in body.get("events", []):
        event_type = event.get("type")
        source = event.get("source", {})

        # ── Only handle group messages ──────────────────────────────────
        if source.get("type") != "group":
            continue

        # ── Optional: filter by target group ────────────────────────────
        if TARGET_GROUP_ID and source.get("groupId") != TARGET_GROUP_ID:
            continue

        # ── Handle join event (bot added to group) ──────────────────────
        if event_type == "join":
            group_id = source.get("groupId", "")
            reply_token = event.get("replyToken", "")
            if reply_token:
                reply_message(reply_token, [
                    {"type": "text", "text": "🎁 三國志兌換 Bot 已加入群組！\n在訊息中 @ 我並附上兌換碼即可自動兌換。"}
                ])
            continue

        # ── Handle message events ───────────────────────────────────────
        if event_type != "message":
            continue

        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        # ── Only respond to @mentions ───────────────────────────────────
        mention = message.get("mention")
        if not mention:
            continue  # not mentioned, ignore

        text = message.get("text", "")
        reply_token = event.get("replyToken", "")
        group_id = source.get("groupId", "")

        # Extract redemption code
        code = extract_code(text)
        if not code:
            reply_message(reply_token, [
                {"type": "text", "text": "⚠️ 請在訊息中附上兌換碼，例如：\n@BotName ABC123XYZ"}
            ])
            continue

        # Load users and redeem
        users = load_users()
        if not users:
            reply_message(reply_token, [
                {"type": "text", "text": "❌ 找不到玩家資料，請確認 user.json 已設定。"}
            ])
            continue

        # Process redemption
        results = []
        success_count = 0
        fail_count = 0

        for user in users:
            ok, msg, _ = process_redemption(user, code, verbose=False)
            name = user.get("player_name", "未知")
            if ok:
                success_count += 1
                results.append(f"✅ {name}: {msg}")
            else:
                fail_count += 1
                results.append(f"❌ {name}: {msg}")

        # Build reply
        summary = f"🎁 兌換碼: {code}\n📊 結果: {success_count} 成功, {fail_count} 失敗\n"
        detail = "\n".join(results)
        reply_text = summary + "\n" + detail

        # LINE message limit: 5000 chars
        if len(reply_text) > 5000:
            reply_text = reply_text[:4997] + "..."

        reply_message(reply_token, [{"type": "text", "text": reply_text}])

    return "OK"


# ── Entry point ─────────────────────────────────────────────────────────

def run_server(host: str = "0.0.0.0", port: int = 5000):
    """Start the webhook server."""
    print(f"[monitor] Starting LINE Bot webhook server on {host}:{port}")
    if TARGET_GROUP_ID:
        print(f"[monitor] Filtered to group: {TARGET_GROUP_ID}")
    else:
        print(f"[monitor] Listening to all groups")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port=port)
