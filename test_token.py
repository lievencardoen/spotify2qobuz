#!/usr/bin/env python3
"""
Quick script to test if your Qobuz token is still valid.
"""

from src.qobuz_client import QobuzClient
from src.utils.credentials import parse_credentials

def test_token():
    print("Testing Qobuz token validity...")
    print()
    
    try:
        # Load credentials
        creds = parse_credentials('credentials.md')
        token = creds.get('QOBUZ_USER_AUTH_TOKEN')
        
        if not token:
            print("❌ No token found in credentials.md")
            return False
        
        print(f"Token found: {token[:20]}...")
        print()
        
        # Test authentication
        client = QobuzClient(token)
        client.authenticate()
        
        print("✅ Token is VALID!")
        print(f"   User: {client.user_name}")
        print(f"   User ID: {client.user_id}")
        print()
        print("You can run the sync without getting a new token.")
        return True
        
    except Exception as e:
        print(f"❌ Token is INVALID or EXPIRED")
        print(f"   Error: {e}")
        print()
        print("You need to get a new token:")
        print("1. Open browser to https://play.qobuz.com and login")
        print("2. Open DevTools (F12) → Network tab")
        print("3. Filter by 'Fetch/XHR'")
        print("4. Play any song or navigate around")
        print("5. Look for X-User-Auth-Token in request headers")
        print("6. Copy the token value to credentials.md")
        print()
        print("See GET_TOKEN_INSTRUCTIONS.md for detailed steps")
        return False

if __name__ == '__main__':
    test_token()
