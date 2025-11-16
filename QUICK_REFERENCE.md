# Quick Reference

## Common Commands

### Playlist Sync
```bash
# Test Qobuz token
python test_token.py

# Dry run (test mode)
python -m src.sync_service --dry-run true

# Run sync (interactive)
python sync.py

# Run sync (direct)
python -m src.sync_service

# Run sync (force new playlists)
python -m src.sync_service --update-existing false
```

### Favorite Sync (NEW!)
```bash
# Dry run (see what would be synced)
python sync_favorites.py --dry-run

# Sync favorites
python sync_favorites.py

# Re-sync all (even if already favorited)
python sync_favorites.py --no-skip-existing
```

## Getting Tokens

### Spotify
1. https://developer.spotify.com/dashboard
2. Create app
3. Add redirect: `http://127.0.0.1:8888/callback`

### Qobuz (HAR method)
1. Open https://play.qobuz.com
2. F12 → Network tab
3. Play a song
4. Right-click → Save as HAR
5. `python extract_token_from_har.py qobuz.har`

## File Locations

| What | Where |
|------|-------|
| Credentials | `credentials.md` |
| Logs | `sync_logs/sync_YYYYMMDD_HHMMSS.log` |
| Reports | `sync_report_YYYYMMDD_HHMMSS.json` |
| Config | `.gitignore` |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Token invalid | `python test_token.py` then get new token |
| Spotify auth failed | Check redirect URI: `127.0.0.1` not `localhost` |
| Duplicates created | Delete in Qobuz, next sync updates existing |
| Slow sync | Normal - ~1 min per playlist |

## Documentation

- **[README.md](README.md)** - Main overview & features
- **[USER_GUIDE.md](USER_GUIDE.md)** - Step-by-step walkthrough
- **[GET_TOKEN_INSTRUCTIONS.md](GET_TOKEN_INSTRUCTIONS.md)** - Detailed token extraction
- **[DUPLICATE_PREVENTION.md](DUPLICATE_PREVENTION.md)** - How duplicates are prevented

## CLI Options

### Playlist Sync
```
--dry-run {true,false}           Test mode (default: false)
--update-existing {true,false}   Prevent duplicates (default: true)
--credentials PATH               Credentials file (default: credentials.md)
--log-file PATH                  Log file (default: auto-generated)
```

### Favorite Sync
```
--dry-run                        Show what would be synced (no changes)
--no-skip-existing               Re-favorite all tracks
--credentials PATH               Credentials file (default: credentials.md)
```

## Expected Results

- **Match rate:** 85-90%
- **Speed:** ~1-2 minutes per playlist
- **Playlist name:** "{name} (from Spotify)"

## Safety Features

✅ Duplicate prevention enabled by default  
✅ Credentials never committed (in .gitignore)  
✅ Logs never committed (in .gitignore)  
✅ Dry-run mode available  
✅ Can run multiple times safely  

## Need Help?

1. Check `sync_logs/` for detailed logs
2. Run `python test_token.py` to test auth
3. Read [USER_GUIDE.md](USER_GUIDE.md) for detailed help
4. Use `--dry-run true` to test without changes
