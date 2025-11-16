#!/usr/bin/env python3
"""
Sync favorite/saved tracks from Spotify to Qobuz.

This script syncs your Spotify saved tracks (liked songs) to Qobuz favorites.
It includes duplicate prevention to avoid re-favoriting tracks that are already
in your Qobuz favorites.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.spotify_client import SpotifyClient
from src.qobuz_client import QobuzClient
from src.favorite_sync_service import FavoriteSyncService
from src.utils.credentials import load_credentials
from src.utils.logger import get_logger


logger = get_logger()


def main():
    """Main entry point for favorite sync."""
    parser = argparse.ArgumentParser(
        description='Sync favorite/saved tracks from Spotify to Qobuz',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be synced without making changes)
  python sync_favorites.py --dry-run
  
  # Sync all favorites
  python sync_favorites.py
  
  # Re-sync all favorites (even if already favorited in Qobuz)
  python sync_favorites.py --no-skip-existing
  
  # Use custom credentials file
  python sync_favorites.py --credentials my_credentials.md
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be synced without making changes'
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Re-favorite tracks even if already in Qobuz favorites'
    )
    
    parser.add_argument(
        '--credentials',
        default='credentials.md',
        help='Path to credentials file (default: credentials.md)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load credentials
        logger.info(f"Loading credentials from {args.credentials}")
        creds = load_credentials(args.credentials)
        
        # Initialize clients
        logger.info("Initializing Spotify client...")
        spotify_client = SpotifyClient(
            client_id=creds['SPOTIPY_CLIENT_ID'],
            client_secret=creds['SPOTIPY_CLIENT_SECRET'],
            redirect_uri=creds['SPOTIPY_REDIRECT_URI']
        )
        
        logger.info("Authenticating with Spotify...")
        spotify_client.authenticate_user()
        
        logger.info("Initializing Qobuz client...")
        qobuz_client = QobuzClient(
            user_auth_token=creds['QOBUZ_USER_AUTH_TOKEN']
        )
        
        logger.info("Authenticating with Qobuz...")
        qobuz_client.authenticate()
        
        # Initialize sync service
        sync_service = FavoriteSyncService(
            spotify_client=spotify_client,
            qobuz_client=qobuz_client
        )
        
        # Perform sync
        mode = "DRY RUN" if args.dry_run else "SYNC"
        skip_mode = "skipping already favorited" if not args.no_skip_existing else "re-favoriting all"
        logger.info(f"\nStarting favorite sync ({mode}, {skip_mode})...\n")
        
        stats = sync_service.sync_favorites(
            dry_run=args.dry_run,
            skip_existing=not args.no_skip_existing
        )
        
        # Exit with appropriate code
        if stats['failed'] > 0:
            logger.warning("\n⚠️  Some tracks failed to sync. Check logs above for details.")
            sys.exit(1)
        elif stats['not_found'] > 0 or stats['skipped_no_match'] > 0:
            logger.info("\n✅ Sync completed with some tracks not found in Qobuz.")
            sys.exit(0)
        else:
            logger.info("\n✅ Favorite sync completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Sync interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
