#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI script to redeem codes via game-notice.qookkagames.com
Usage: 
  Manual mode: python main.py --code <code>
  Monitor mode: python main.py --monitor [--port <port>]
"""

import argparse
import importlib
import json
import os
import sys

from redeem import process_redemption

def default_users_file():
    return os.environ.get(
        "SANGUO_USERS_FILE",
        os.path.join(os.path.dirname(__file__), "user.json")
    )

def load_users(users_file=None):
    """Load user data from the configured user.json path."""
    users_file = users_file or default_users_file()
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        return users
    except FileNotFoundError:
        print(f"Error: {users_file} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {users_file}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Redeem codes for game-notice.qookkagames.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Manual redemption for all users
  python main.py --code "ABC123XYZ"
  
  # Manual redemption for specific user
  python main.py --code "ABC123XYZ" --user-index 0
  
  # Start monitoring mode (LINE Bot webhook)
  python main.py --monitor
  
  # Start monitoring mode on custom port
  python main.py --monitor --port 8080
        """
    )
    
    # Mode selection
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Start monitoring mode (LINE Bot webhook server)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for monitoring mode webhook server (default: 5000)"
    )
    
    # Manual mode arguments
    parser.add_argument(
        "--code",
        type=str,
        default=None,
        help="The redemption code (supports Chinese/Unicode) - required for manual mode"
    )
    parser.add_argument(
        "--user-index",
        type=int,
        default=None,
        help="Index of user in hkusers.json (default: redeem for all users)"
    )
    parser.add_argument(
        "--users-file",
        type=str,
        default=None,
        help="Path to user.json (default: SANGUO_USERS_FILE or ./user.json)"
    )
    
    args = parser.parse_args()
    
    # If monitor mode, start webhook server
    if args.monitor:
        try:
            monitor = importlib.import_module("monitor")
        except ImportError:
            print(
                "Error: monitor mode requires monitor.py, which is not included in this skill.",
                file=sys.stderr
            )
            sys.exit(1)
        monitor.run_server(port=args.port)
        return
    
    # Manual mode - require code
    if not args.code:
        parser.error("--code is required for manual mode (or use --monitor for monitoring mode)")
    
    # Load users from JSON
    users = load_users(args.users_file)
    
    if not users:
        print("Error: user.json is empty", file=sys.stderr)
        sys.exit(1)
    
    # Determine which users to process
    if args.user_index is not None:
        if args.user_index >= len(users):
            print(f"Error: user index {args.user_index} out of range (max: {len(users) - 1})", file=sys.stderr)
            sys.exit(1)
        users_to_process = [users[args.user_index]]
    else:
        users_to_process = users
    
    code = args.code
    
    print(f"🎁 Redeeming code: {code}")
    print(f"👥 Processing {len(users_to_process)} user(s)")
    print("=" * 50)
    
    success_count = 0
    fail_count = 0
    
    for i, user in enumerate(users_to_process):
        success, message, details = process_redemption(user, code, verbose=True)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count} success, {fail_count} failed")
    
    if fail_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
