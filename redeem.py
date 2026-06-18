#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core redemption logic shared between CLI and monitoring mode
"""

import json
import requests

# API endpoint (discovered from network inspection)
API_URL = "https://p10527-game-adapter.qookkagames.com/cms/active_code/change"
FORM_URL = "https://game-notice.qookkagames.com/64103079d26d1f0ace5fb304/index"


def redeem_code(player_id, player_name, code, region="hk"):
    """Submit redemption request to the API"""
    payload = {
        "player_name": player_name,
        "player_id": player_id,
        "code": code,
        "region": region,
    }

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://game-notice.qookkagames.com",
        "Referer": FORM_URL,
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/135.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        return response
    except requests.exceptions.RequestException:
        return None


def process_redemption(user, code, verbose=True):
    """
    Process redemption for a single user

    Args:
        user: dict with player_id and player_name
        code: redemption code string
        verbose: whether to print output

    Returns:
        tuple: (success: bool, message: str, details: dict)
    """
    player_id = user.get("player_id")
    player_name = user.get("player_name")
    region = user.get("region", "hk")

    if not player_id or not player_name:
        return False, "Missing player_id or player_name", {}

    if verbose:
        print(f"\n📤 User: {player_name} (ID: {player_id}, Region: {region})")

    response = redeem_code(player_id, player_name, code, region)

    if response is None:
        if verbose:
            print("   ❌ Request failed")
        return False, "Request failed", {}

    if verbose:
        print(f"   Status: {response.status_code}")

    try:
        resp_json = response.json()
        if verbose:
            print(f"   Response: {json.dumps(resp_json, ensure_ascii=False, indent=2)}")

        if response.status_code == 200 and resp_json.get("code") == 200:
            items = resp_json.get("items", [])
            if items:
                reward_desc = items[0].get("reward_desc", {})
                subject = reward_desc.get("subject", "")
                body_text = reward_desc.get("body", "")
                msg = f"{subject}: {body_text}" if subject or body_text else "Success"
                if verbose:
                    print(f"   ✅ Success! {msg}")
                return True, msg, resp_json
            else:
                if verbose:
                    print("   ✅ Success!")
                return True, "Success", resp_json
        else:
            msg = resp_json.get("message") or resp_json.get("msg") or "Unknown error"
            if verbose:
                print(f"   ❌ Failed: {msg}")
            return False, msg, resp_json

    except json.JSONDecodeError:
        if verbose:
            print(f"   Response text: {response.text}")
        success = response.status_code == 200
        return success, response.text, {}
