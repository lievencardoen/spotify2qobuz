# Favorite Track Syncing

## Overview

The favorite sync feature allows you to sync your Spotify "Liked Songs" (saved tracks) to Qobuz favorites. This is a separate operation from playlist syncing and can be run independently.

## How It Works

1. **Fetches Saved Tracks** - Retrieves all tracks you've liked/saved in Spotify
2. **Searches Qobuz** - For each track, searches the Qobuz catalog
3. **Matches Tracks** - Uses fuzzy matching (title, artist) to find the best match
4. **Adds to Favorites** - Marks matched tracks as favorites in Qobuz
5. **Prevents Duplicates** - By default, skips tracks already favorited in Qobuz

## Usage

### Basic Sync

```bash
python sync_favorites.py
```

This will:
- Fetch all your Spotify saved tracks
- Get your existing Qobuz favorites
- Match and favorite new tracks
- Skip tracks already favorited

### Dry Run (Preview)

```bash
python sync_favorites.py --dry-run
```

Shows what would be synced without making any changes. Perfect for testing.

### Re-sync All Favorites

```bash
python sync_favorites.py --no-skip-existing
```

Re-favorites all tracks, even if they're already in your Qobuz favorites.

### Custom Credentials

```bash
python sync_favorites.py --credentials my_credentials.md
```

Use a different credentials file.

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run` | Preview changes without syncing | Off |
| `--no-skip-existing` | Re-favorite already favorited tracks | Off (skips existing) |
| `--credentials PATH` | Path to credentials file | `credentials.md` |

## What to Expect

### First Run

```
Fetching saved tracks from Spotify...
Found 523 saved tracks in Spotify
Fetching existing Qobuz favorites to avoid duplicates...
Found 412 existing favorites in Qobuz

[1/523] Processing: The Beatles - Here Comes The Sun
  ✅ Favorited: The Beatles - Here Comes The Sun

[2/523] Processing: Pink Floyd - Comfortably Numb
  ⏭️  Already favorited: Pink Floyd - Comfortably Numb

...

FAVORITE SYNC SUMMARY
==================================================
Total Spotify saved tracks: 523
Already favorited in Qobuz: 412
Successfully matched & favorited: 98
Not found in Qobuz: 13
No good match found: 0
Failed to add: 0
Success rate: 88.3%
==================================================
```

### Subsequent Runs

Much faster! Only processes tracks that aren't already favorited in Qobuz.

## Features

### Smart Duplicate Prevention

- Fetches existing Qobuz favorites before syncing
- Skips tracks already favorited
- Only favorites new tracks
- Safe to run multiple times

### High-Quality Matching

Uses fuzzy string matching with:
- **Title matching** (60% weight)
- **Artist matching** (40% weight)
- **Threshold:** 70% minimum similarity score

### Error Handling

- Gracefully handles tracks not found in Qobuz
- Logs all errors for review
- Continues syncing even if some tracks fail
- Exit codes: 0 (success), 1 (some failures), 130 (interrupted)

### Detailed Logging

All operations are logged to `sync_logs/` with:
- Track-by-track progress
- Match details
- Error messages
- Summary statistics

## Integration with Spotify

### OAuth Scope

The sync now requests the `user-library-read` scope from Spotify, which allows:
- Reading your saved/liked tracks
- Accessing your library
- No write permissions (read-only)

### First Run Authentication

On first run, Spotify will ask you to approve the additional permission. This is a one-time approval.

## API Endpoints Used

### Spotify API

- `current_user_saved_tracks` - Fetches liked songs (paginated)

### Qobuz API

- `GET /favorite/getUserFavorites?type=tracks` - Gets existing favorites
- `POST /favorite/create?track_ids={id}` - Adds track to favorites

## Implementation Details

### Files Added

1. **`src/favorite_sync_service.py`** - Core sync logic
2. **`sync_favorites.py`** - CLI script
3. **`tests/test_favorite_sync_service.py`** - Comprehensive tests

### Files Modified

1. **`src/spotify_client.py`** - Added `get_saved_tracks()` method
2. **`src/qobuz_client.py`** - Added favorite track methods
3. **`src/matcher.py`** - Added `find_best_match()` helper function

### Test Coverage

- **28 new tests** added
- **116 total tests**
- **91% code coverage**
- All tests passing ✅

## Comparison with Playlist Sync

| Feature | Playlist Sync | Favorite Sync |
|---------|--------------|---------------|
| **What it syncs** | All playlists | Liked/saved tracks |
| **Destination** | Qobuz playlists | Qobuz favorites |
| **Naming** | "{name} (from Spotify)" | Native favorites |
| **Duplicate check** | Per playlist | All favorites |
| **Speed** | ~1 min per playlist | ~1-2 sec per track |
| **Updates** | Adds new tracks | Adds new favorites |

## Tips

### When to Use

- ✅ Sync your "Liked Songs" collection
- ✅ Keep favorites in sync across platforms
- ✅ Backup your Spotify library to Qobuz

### When NOT to Use

- ❌ If you want to organize favorites into playlists (use playlist sync instead)
- ❌ If Qobuz favorites is for different music than Spotify

### Best Practices

1. **Run dry-run first** - See what will be synced
2. **Check logs** - Review match quality in `sync_logs/`
3. **Run periodically** - Keep favorites in sync (monthly/weekly)
4. **Safe to interrupt** - Press Ctrl+C anytime, run again later

## Troubleshooting

### "No saved tracks found in Spotify"

You don't have any liked songs in Spotify. Go to Spotify and like some songs first.

### "Failed to get favorite tracks"

Your Qobuz token may be expired. Run `python test_token.py` to check, then get a new token if needed.

### "Track not found in Qobuz"

The track doesn't exist in Qobuz's catalog. This is normal for:
- Exclusive releases
- Regional variations
- Unreleased tracks
- Removed content

### High "Not found" rate

If many tracks aren't found:
1. Check if they're actually in Qobuz catalog
2. Try searching manually in Qobuz web player
3. Review `sync_logs/` for specific track names

## Future Enhancements

Possible improvements for future versions:
- Sync Spotify albums to Qobuz favorites
- Sync Spotify artists to Qobuz favorites
- Incremental sync (only new saves since last run)
- Batch favorite operations (faster)
- Remove unfavorited tracks from Qobuz

## Example Workflow

### Complete Sync (Playlists + Favorites)

```bash
# 1. Sync playlists
python sync.py

# 2. Sync favorites
python sync_favorites.py

# Done! Your entire Spotify library is now in Qobuz
```

### Update After Adding New Music

```bash
# Re-run both syncs (smart duplicate prevention)
python sync.py                  # Updates playlists
python sync_favorites.py         # Adds new favorites
```

## Support

If you encounter issues:

1. **Check logs** - `sync_logs/sync_*.log` has detailed information
2. **Test token** - `python test_token.py` verifies authentication
3. **Dry run** - `python sync_favorites.py --dry-run` tests without changes
4. **Review docs** - `USER_GUIDE.md` has troubleshooting tips

---

**Happy syncing! Your favorites are waiting in Qobuz! ⭐**
