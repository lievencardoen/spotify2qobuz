import json
import sys

if len(sys.argv) < 2:
    print("Usage: python extract_token_from_har.py <path/to/qobuz.har>")
    sys.exit(1)

har_path = sys.argv[1]

# Read HAR file
with open(har_path, 'r') as f:
    har_data = json.load(f)

print("=" * 60)
print("Searching for Qobuz Authentication Token")
print("=" * 60)
print()

token = None
found_in = None

# Search through all entries
for entry in har_data['log']['entries']:
    # Check request headers
    if 'request' in entry and 'headers' in entry['request']:
        for header in entry['request']['headers']:
            if header['name'].lower() in ['x-user-auth-token', 'authorization', 'x-auth-token']:
                token = header['value']
                found_in = f"Request header: {header['name']}"
                break
    
    # Check request cookies
    if 'request' in entry and 'cookies' in entry['request']:
        for cookie in entry['request']['cookies']:
            if 'user_auth_token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                if len(cookie.get('value', '')) > 30:
                    token = cookie['value']
                    found_in = f"Request cookie: {cookie['name']}"
                    break
    
    # Check response cookies
    if 'response' in entry and 'cookies' in entry['response']:
        for cookie in entry['response']['cookies']:
            if 'user_auth_token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                if len(cookie.get('value', '')) > 30:
                    token = cookie['value']
                    found_in = f"Response cookie: {cookie['name']}"
                    break
    
    if token:
        break

if token:
    print(f"✅ Found token in: {found_in}")
    print()
    print("Token:")
    print("-" * 60)
    print(token)
    print("-" * 60)
    print()
    
    # Try to update credentials.md
    try:
        with open('credentials.md', 'r') as f:
            content = f.read()
        
        if 'QOBUZ_USER_AUTH_TOKEN=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('QOBUZ_USER_AUTH_TOKEN='):
                    lines[i] = f'QOBUZ_USER_AUTH_TOKEN={token}'
                    break
            content = '\n'.join(lines)
            
            with open('credentials.md', 'w') as f:
                f.write(content)
            
            print("✅ Updated credentials.md with your token!")
        else:
            print("⚠️  Please manually add this to credentials.md:")
            print(f"   QOBUZ_USER_AUTH_TOKEN={token}")
    except Exception as e:
        print(f"⚠️  Could not update credentials.md: {e}")
        print("   Please copy the token above manually")
else:
    print("❌ Could not find authentication token in HAR file")
    print()
    print("This might mean:")
    print("  - You weren't fully logged in when you exported the HAR")
    print("  - The token is stored differently than expected")
    print()
    print("Let me show you all cookies found:")
    print()
    
    all_cookies = set()
    for entry in har_data['log']['entries']:
        if 'request' in entry and 'cookies' in entry['request']:
            for cookie in entry['request']['cookies']:
                all_cookies.add(f"{cookie['name']}: {cookie.get('value', '')[:60]}...")
    
    for cookie in sorted(all_cookies):
        print(f"  {cookie}")
