"""Service for syncing favorite tracks from Spotify to Qobuz."""

from typing import Dict, List, Tuple
from src.spotify_client import SpotifyClient
from src.qobuz_client import QobuzClient
from src.matcher import find_best_match
from src.utils.logger import get_logger


logger = get_logger()


class FavoriteSyncService:
    """Service for syncing favorite/saved tracks from Spotify to Qobuz."""
    
    def __init__(self, spotify_client: SpotifyClient, qobuz_client: QobuzClient):
        """
        Initialize favorite sync service.
        
        Args:
            spotify_client: Authenticated Spotify client
            qobuz_client: Authenticated Qobuz client
        """
        self.spotify_client = spotify_client
        self.qobuz_client = qobuz_client
    
    def sync_favorites(self, dry_run: bool = False, skip_existing: bool = True) -> Dict:
        """
        Sync all saved/liked tracks from Spotify to Qobuz favorites.
        
        Args:
            dry_run: If True, only report what would be synced without making changes
            skip_existing: If True, skip tracks that are already favorited in Qobuz
        
        Returns:
            Dict with sync statistics:
            - total_spotify_favorites: Total number of Spotify saved tracks
            - already_favorited: Number of tracks already in Qobuz favorites
            - matched: Number of tracks successfully matched and favorited
            - not_found: Number of tracks that couldn't be found in Qobuz
            - failed: Number of tracks that failed to add to favorites
        """
        logger.info("Starting favorite tracks sync from Spotify to Qobuz")
        
        # Get saved tracks from Spotify
        logger.info("Fetching saved tracks from Spotify...")
        spotify_tracks = self.spotify_client.get_saved_tracks()
        
        stats = {
            'total_spotify_favorites': len(spotify_tracks),
            'already_favorited': 0,
            'matched': 0,
            'not_found': 0,
            'failed': 0,
            'skipped_no_match': 0
        }
        
        if stats['total_spotify_favorites'] == 0:
            logger.info("No saved tracks found in Spotify")
            return stats
        
        logger.info(f"Found {stats['total_spotify_favorites']} saved tracks in Spotify")
        
        # Get existing Qobuz favorites if skip_existing is enabled
        existing_favorites = set()
        if skip_existing:
            logger.info("Fetching existing Qobuz favorites to avoid duplicates...")
            try:
                existing_favorites = set(self.qobuz_client.get_favorite_tracks())
                logger.info(f"Found {len(existing_favorites)} existing favorites in Qobuz")
            except Exception as e:
                logger.warning(f"Could not fetch existing favorites: {e}. Proceeding without duplicate check.")
        
        # Process each track
        for i, spotify_track in enumerate(spotify_tracks, 1):
            track_name = spotify_track['title']
            artist_name = spotify_track['artist']
            
            logger.info(f"[{i}/{stats['total_spotify_favorites']}] Processing: {artist_name} - {track_name}")
            
            # Search for track in Qobuz
            try:
                search_results = self.qobuz_client.search_track(
                    title=track_name,
                    artist=artist_name
                )
                
                if not search_results:
                    logger.warning(f"  ❌ Not found in Qobuz: {artist_name} - {track_name}")
                    stats['not_found'] += 1
                    continue
                
                # Find best match
                best_match = find_best_match(spotify_track, search_results)
                
                if not best_match:
                    logger.warning(f"  ⚠️  No good match found for: {artist_name} - {track_name}")
                    stats['skipped_no_match'] += 1
                    continue
                
                qobuz_track_id = best_match['id']
                
                # Check if already favorited
                if skip_existing and qobuz_track_id in existing_favorites:
                    logger.info(f"  ⏭️  Already favorited: {artist_name} - {track_name}")
                    stats['already_favorited'] += 1
                    continue
                
                # Add to favorites (or simulate in dry run)
                if dry_run:
                    logger.info(f"  [DRY RUN] Would favorite: {artist_name} - {track_name} (ID: {qobuz_track_id})")
                    stats['matched'] += 1
                else:
                    success = self.qobuz_client.add_favorite_track(qobuz_track_id)
                    if success:
                        logger.info(f"  ✅ Favorited: {artist_name} - {track_name}")
                        stats['matched'] += 1
                    else:
                        logger.error(f"  ❌ Failed to favorite: {artist_name} - {track_name}")
                        stats['failed'] += 1
                        
            except Exception as e:
                logger.error(f"  ❌ Error processing track: {e}")
                stats['failed'] += 1
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("FAVORITE SYNC SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Spotify saved tracks: {stats['total_spotify_favorites']}")
        logger.info(f"Already favorited in Qobuz: {stats['already_favorited']}")
        logger.info(f"Successfully matched & favorited: {stats['matched']}")
        logger.info(f"Not found in Qobuz: {stats['not_found']}")
        logger.info(f"No good match found: {stats['skipped_no_match']}")
        logger.info(f"Failed to add: {stats['failed']}")
        
        success_rate = 0
        if stats['total_spotify_favorites'] > 0:
            # Calculate success rate (matched / total that weren't already favorited)
            to_process = stats['total_spotify_favorites'] - stats['already_favorited']
            if to_process > 0:
                success_rate = (stats['matched'] / to_process) * 100
        
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info("="*60)
        
        return stats
