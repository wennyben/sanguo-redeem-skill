---
name: sanguo-redeem
description: Redeem Sanguo game gift codes for configured HK users. Use when the user mentions 三國志,三國,Sanguo,禮包碼,兌換碼,redemption codes, or asks to redeem a code.
---

# Sanguo Redeem

Use this skill to redeem a Sanguo gift code for the configured HK player list.

This skill is mounted read-only from the git repo at `/opt/data/skills/sanguo`. Hermes keeps bundled skills in the same parent directory; do not try to edit skill files inside the container. Change the repo on the host, then redeploy or recreate the container.

## Quick Start

Run inside the Hermes container:

```bash
python3 /opt/data/skills/sanguo/main.py --code "CODE_HERE"
```

For one player only, use the zero-based index from the configured users file:

```bash
python3 /opt/data/skills/sanguo/main.py --code "CODE_HERE" --user-index 0
```

## Managing `user.json`

The real `user.json` is account data, not skill source. Keep it outside git at:

```bash
/opt/data/sanguo/user.json
```

The container sets `SANGUO_USERS_FILE=/opt/data/sanguo/user.json`, so the script loads that file by default. For local testing, either set `SANGUO_USERS_FILE` or pass `--users-file`.

Use `hkusers.example.json` only as the schema template:

```json
[
  {
    "player_id": "123456",
    "player_name": "玩家A",
    "region": "hk"
  }
]
```

Do not commit, print, or paste the full real player list unless the user explicitly asks. If the users file is missing, ask the user for the player records or ask them to create it from `hkusers.example.json`.

<!-- SAFETY-CHECK: writable edit test -->

## Result Handling

- If all users succeed, summarize the success count and any reward text.
- If some users fail, report the failed player names and API messages.
- If the API says `code has been used`, treat it as a normal already-redeemed result, not an infrastructure failure.
- If `player not found` appears, tell the user the `player_id` or exact `player_name` likely needs correction.
