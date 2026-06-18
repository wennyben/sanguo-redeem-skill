#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Basic tests for the redemption module."""

import json
from unittest.mock import patch, MagicMock
from redeem import process_redemption, redeem_code


def test_redeem_code_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": 200,
        "items": [{"reward_desc": {"subject": "Test", "body": "Reward"}}],
    }
    with patch("redeem.requests.post", return_value=mock_resp):
        resp = redeem_code("123", "TestPlayer", "CODE")
        assert resp is not None
        assert resp.status_code == 200


def test_process_redemption_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": 200,
        "items": [{"reward_desc": {"subject": "Gift", "body": "100 gems"}}],
    }
    with patch("redeem.requests.post", return_value=mock_resp):
        user = {"player_id": "123", "player_name": "TestPlayer", "region": "hk"}
        ok, msg, details = process_redemption(user, "CODE", verbose=False)
        assert ok is True
        assert "Gift" in msg


def test_process_redemption_missing_fields():
    user = {"player_id": "", "player_name": ""}
    ok, msg, details = process_redemption(user, "CODE", verbose=False)
    assert ok is False
    assert "Missing" in msg


if __name__ == "__main__":
    test_redeem_code_success()
    test_process_redemption_success()
    test_process_redemption_missing_fields()
    print("✅ All tests passed")
