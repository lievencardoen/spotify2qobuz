# Spotify to Qobuz Playlist Sync

Automatically sync all your Spotify playlists to Qobuz with intelligent duplicate prevention and high-quality track matching.

## ✨ Features

- 🎵 **Sync all playlists** from Spotify to Qobuz
- ⭐ **Sync favorite/saved tracks** from Spotify to Qobuz
- 🔄 **Smart duplicate prevention** - run multiple times without creating duplicates
- 🎯 **High accuracy matching** (89%+ success rate)
  - ISRC-based matching (most accurate)
  - Fuzzy matching fallback for tracks without ISRC
- 🔐 **Token-based authentication** - works with any Qobuz account (email, Google, Facebook, etc.)
- 📊 **Detailed reporting** - JSON reports with match statistics
- 🪵 **Comprehensive logging** - auto-generated timestamped logs
- 🧪 **Well tested** - 116 unit tests, 91% code coverage
- 🚀 **Fast and efficient** - leverages ISRC codes for instant matching

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Your Credentials

#### Spotify (Easy)
1. Go to https://developer.spotify.com/dashboard
2. Create an app, copy Client ID and Secret
3. Add redirect URI: `http://127.0.0.1:8888/callback`

#### Qobuz (Use HAR File - Recommended)
1. Open https://play.qobuz.com and login
2. Open DevTools (F12) → Network tab
3. Play a song or browse playlists
4. Right-click in Network tab → "Save all as HAR"
5. Save as `qobuz.har`
6. Run: `python extract_token_from_har.py qobuz.har`

See [GET_TOKEN_INSTRUCTIONS.md](GET_TOKEN_INSTRUCTIONS.md) for detailed steps.

### 3. Configure credentials.md

```markdown
## Spotify
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

## Qobuz
QOBUZ_USER_AUTH_TOKEN=your_token_here
```

### 4. Test Your Setup

```bash
# Test Qobuz token
python test_token.py

# Dry run (see what would happen, no changes made)
python -m src.sync_service --dry-run true
```

### 5. Run the Sync!

```bash
python sync.py
```

That's it! Your playlists will be synced to Qobuz with the suffix "(from Spotify)".

## 🔄 Running Again (No Duplicates!)

**You can run the sync as many times as you want** - it won't create duplicates!

```bash
python sync.py
```

What happens:
- ✅ Finds existing playlists in Qobuz
- ✅ Checks which tracks are already there
- ✅ Only adds NEW tracks
- ✅ Skips duplicates
- ✅ Updates playlists if you added songs to Spotify

Example output:
```
Found existing playlist with 39 tracks, will add missing tracks only
Playlist sync complete: 80s - 40/43 tracks matched, 35 already in playlist
```

See [DUPLICATE_PREVENTION.md](DUPLICATE_PREVENTION.md) for technical details.

## 📋 Usage Examples

### Sync Playlists
```bash
# Interactive mode with confirmation
python sync.py

# Direct sync
python -m src.sync_service
```

### Sync Favorites (NEW!)
```bash
# Sync your Spotify saved tracks to Qobuz favorites
python sync_favorites.py

# Dry run to see what would be synced
python sync_favorites.py --dry-run

# Re-sync all favorites (even if already favorited)
python sync_favorites.py --no-skip-existing
```

### Dry Run (Test Mode)
```bash
# Playlists - see what would happen without making changes
python -m src.sync_service --dry-run true

# Favorites - see what would be synced
python sync_favorites.py --dry-run
```

### Force Create New Playlists
```bash
# Create new playlists even if they exist (will create duplicates)
python -m src.sync_service --update-existing false
```

### Custom Credentials File
```bash
# Playlists
python -m src.sync_service --credentials my_creds.md

# Favorites
python sync_favorites.py --credentials my_creds.md
```

### Custom Log File
```bash
python -m src.sync_service --log-file my_sync.log
```

## 📊 Command Line Options

### Playlist Sync Options
```bash
python -m src.sync_service [options]

Options:
  --dry-run {true,false}
      Test mode - no changes made (default: false)
      
  --update-existing {true,false}
      Update existing playlists instead of creating duplicates (default: true)
      ⚠️  Set to false only if you want duplicate playlists
      
  --credentials PATH
      Path to credentials file (default: credentials.md)
      
  --log-file PATH
      Path to log file (default: auto-generated sync_logs/sync_YYYYMMDD_HHMMSS.log)
```

### Favorite Sync Options
```bash
python sync_favorites.py [options]

Options:
  --dry-run
      Show what would be synced without making changes
      
  --no-skip-existing
      Re-favorite tracks even if already in Qobuz favorites
      
  --credentials PATH
      Path to credentials file (default: credentials.md)
```

## 📈 What to Expect

### First Sync
- **121 playlists synced** (example from real usage)
- **5,016 tracks matched** (89.25% success rate)
- **4,847 ISRC matches** (instant, perfect matches)
- **169 fuzzy matches** (name/artist/duration matching)
- **604 tracks not found** (missing from Qobuz catalog)
- **Time:** ~1.5 hours for 121 playlists

### Second Sync (Update)
- Finds all 121 existing playlists
- Checks existing tracks
- Adds only new tracks since last sync
- **Much faster** - only processes new tracks

## 🎯 How Track Matching Works

1. **ISRC Match (Best)** - Uses International Standard Recording Code
   - Instant, exact match
   - ~96% of tracks have ISRC codes
   - Most reliable method

2. **Fuzzy Match (Fallback)** - Uses title, artist, duration
   - RapidFuzz algorithm (Levenshtein distance)
   - Matches similar spellings, feat. variations
   - Score threshold: 85+

3. **Not Found** - Track doesn't exist in Qobuz catalog
   - Logged in missing tracks report
   - Saved to JSON for review

## 📁 Project Structure

```
SpotifyQobuzSync/
├── src/
│   ├── spotify_client.py         # Spotify API integration
│   ├── qobuz_client.py           # Qobuz API integration  
│   ├── matcher.py                # ISRC + fuzzy matching
│   ├── sync_service.py           # Playlist sync orchestration
│   ├── favorite_sync_service.py  # Favorite sync orchestration
│   └── utils/
│       ├── credentials.py        # Credential parsing
│       └── logger.py             # Logging setup
├── tests/                        # 116 unit tests
├── sync_logs/                    # Auto-generated logs
├── credentials.md                # Your API credentials (gitignored)
├── sync.py                       # Playlist sync script
├── sync_favorites.py             # Favorite sync script
├── test_token.py                 # Test Qobuz token validity
├── extract_token_from_har.py     # Extract token from HAR file
├── README.md                     # This file
├── GET_TOKEN_INSTRUCTIONS.md   # Detailed token guide
└── DUPLICATE_PREVENTION.md     # Technical duplicate prevention info
```

## 🔧 Development

### Run Tests
```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Project Stats
- **Lines of Code:** ~1,500
- **Test Coverage:** 92%
- **Tests:** 88 passing
- **Match Rate:** 89%+ on real playlists

## 🐛 Troubleshooting

### Token Invalid/Expired
```
❌ Invalid or expired Qobuz token
```

**Solution:** Get a new token using the HAR file method:
1. Visit https://play.qobuz.com (login)
2. F12 → Network tab → Play a song
3. Right-click → "Save all as HAR"
4. Run: `python extract_token_from_har.py qobuz.har`
5. Update `credentials.md`

Test your token:
```bash
python test_token.py
```

### Spotify Authentication Failed
```
INVALID_CLIENT: Invalid redirect URI
```

**Solution:** Make sure redirect URI is exactly:
```
http://127.0.0.1:8888/callback
```
(Use `127.0.0.1` NOT `localhost`)

### Duplicate Playlists Created
If you accidentally created duplicates:

1. **Manually delete** duplicate playlists in Qobuz web player
2. **Next sync will update** the remaining playlists (no more duplicates)

The default `--update-existing true` prevents this.

### Token Expiration
Qobuz tokens typically last **days to weeks**. Test before syncing:
```bash
python test_token.py
```

## 🤝 Contributing

This project was built with AI assistance (GitHub Copilot). Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Built with Python 3.13
- Spotify Web API via [Spotipy](https://github.com/spotipy-dev/spotipy)
- Track matching via [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- Qobuz undocumented API (token-based authentication)

## 📞 Support

For issues or questions:
1. Check [GET_TOKEN_INSTRUCTIONS.md](GET_TOKEN_INSTRUCTIONS.md)
2. Check [DUPLICATE_PREVENTION.md](DUPLICATE_PREVENTION.md)
3. Review log files in `sync_logs/`
4. Check JSON reports: `sync_report_*.json`

---

**Happy Syncing! 🎵→🎵**
