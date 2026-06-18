---
name: sanguo-redeem
description: Redeem Sanguo game gift codes for configured HK users. Use when the user mentions 三國志,三國,Sanguo,禮包碼,兌換碼,redemption codes, or asks to redeem a code.
---

# Sanguo Redeem

Use this skill to redeem a Sanguo gift code for the configured player list.

## Quick Start

```bash
# Manual redemption for all users
.venv/bin/python main.py --code "CODE_HERE"

# Redeem for one player only (zero-based index)
.venv/bin/python main.py --code "CODE_HERE" --user-index 0
```

Always use `.venv/bin/python` from the skill directory — the system Python does **not** have `requests` / `flask`.

## Dependency Management

The skill has its own `.venv` at the skill root with `requests` + `flask` installed via `uv`:

```bash
cd /opt/data/skills/sanguo
uv venv .venv
uv pip install --python .venv/bin/python requests flask
```

The `start_linebot.sh` script and all runtime invocations point to this `.venv`. If the venv is accidentally deleted, just re-run the two commands above — no host-level Docker changes needed.

## Managing `user.json`

The real `user.json` is account data, not skill source. Keep it outside git at:

```bash
/opt/data/sanguo/user.json
```

The container sets `SANGUO_USERS_FILE=/opt/data/sanguo/user.json`, so the script loads that file by default. For local testing, either set `SANGUO_USERS_FILE` or pass `--users-file`.

Use `users.example.json` only as the schema template:

```json
[
  {
    "player_id": "123456",
    "player_name": "玩家A",
    "region": "hk"
  }
]
```

Do not commit, print, or paste the full real player list unless the user explicitly asks. If the users file is missing, ask the user for the player records or ask them to create it from `users.example.json`.

## LINE Bot Monitor Mode

```bash
# Start the LINE Bot webhook server (background, nohup)
bash start_linebot.sh

# Check status
cat /tmp/linebot.pid && tail -f /tmp/linebot.log

# Stop
kill $(cat /tmp/linebot.pid)
```

### Auto-restart on container reboot

A Hermes cron job ("LINE Bot watchdog") runs every minute. It checks if the LINE Bot process is alive via `/tmp/linebot.pid`. If the process died (e.g. after container restart), it automatically restarts `main.py --monitor` using the skill's `.venv`.

The watchdog script is at `linebot_watchdog.sh`. To verify the cron job is active:

```bash
hermes cron list
```

If the venv is missing after a container rebuild, the watchdog will report an error. Fix by re-creating the venv:

```bash
cd /opt/data/skills/sanguo
uv venv .venv
uv pip install --python .venv/bin/python requests flask
```

Monitor mode only responds to `@mentions` in group chats. DMs are ignored.

Required env vars (or set in `line_config.json`):
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_TARGET_GROUP_ID` (optional — restricts to one group, legacy)
- `LINE_ALLOWED_GROUPS` (optional — JSON array of group IDs, e.g. `["C123..."]`)
- `LINE_ALLOWED_USERS` (optional — JSON array of user IDs, e.g. `["U123..."]`)

The webhook listens on port 5000 (internal) by default.

## Files

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point (manual redeem / monitor mode) |
| `redeem.py` | Core redemption API logic |
| `monitor.py` | LINE Bot webhook server (Flask) |
| `start_linebot.sh` | Start monitor in background with nohup |
| `linebot_watchdog.sh` | Watchdog script — checks if LINE Bot is alive, restarts if not |
| `line_config.json` | LINE credentials (create from `line_config.json.example`) |
| `users.example.json` | Schema template for user.json |

## Result Handling

- If all users succeed, summarize the success count and any reward text.
- If some users fail, report the failed player names and API messages.
- If the API says `code has been used`, treat it as a normal already-redeemed result, not an infrastructure failure.
- If `player not found` appears, tell the user the `player_id` or exact `player_name` likely needs correction.
