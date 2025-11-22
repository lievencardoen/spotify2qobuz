#!/usr/bin/env python3
"""Retry failed playlist syncs based on log file analysis."""

import argparse
import re
from pathlib import Path
from typing import List, Set
from src.sync_service import SyncService
from src.utils.logger import get_logger

logger = get_logger()


def parse_log_file(log_path: str) -> Set[str]:
    """
    Parse log file to extract playlists with errors or failed tracks.
    
    Args:
        log_path: Path to log file
        
    Returns:
        Set of playlist names that had issues
    """
    failed_playlists = set()
    
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find playlists with errors using the "Error syncing playlist" pattern
    sync_error_pattern = r'Error syncing playlist[:\s]+([^:]+)'
    for match in re.finditer(sync_error_pattern, content):
        playlist_name = match.group(1).strip()
        if playlist_name:
            failed_playlists.add(playlist_name)
    
    # Find playlists with connection errors during sync
    syncing_pattern = r'Syncing playlist: (.+?) \(\d+ tracks\)'
    error_after_pattern = r'ERROR.*?(?:timeout|Connection|aborted)'
    
    lines = content.split('\n')
    current_playlist = None
    
    for i, line in enumerate(lines):
        # Track which playlist is being synced
        sync_match = re.search(syncing_pattern, line)
        if sync_match:
            current_playlist = sync_match.group(1)
        
        # If we see an error and we know the current playlist, mark it
        if current_playlist and re.search(error_after_pattern, line):
            failed_playlists.add(current_playlist)
    
    return failed_playlists


def get_latest_log_file(log_dir: str = "sync_logs") -> Path:
    """
    Get the most recent log file.
    
    Args:
        log_dir: Directory containing log files
        
    Returns:
        Path to latest log file
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        raise FileNotFoundError(f"Log directory not found: {log_dir}")
    
    log_files = list(log_path.glob("sync_*.log"))
    if not log_files:
        raise FileNotFoundError(f"No log files found in {log_dir}")
    
    # Sort by modification time and get the latest
    latest = max(log_files, key=lambda p: p.stat().st_mtime)
    return latest


def retry_failed_playlists(
    failed_playlists: Set[str],
    dry_run: bool = False,
    credentials_path: str = "credentials.md"
):
    """
    Retry syncing playlists that had errors.
    
    Args:
        failed_playlists: Set of playlist names to retry
        dry_run: If True, don't actually make changes
        credentials_path: Path to credentials file
    """
    if not failed_playlists:
        logger.info("No failed playlists found to retry")
        return
    
    logger.info(f"Found {len(failed_playlists)} playlists with errors:")
    for playlist in sorted(failed_playlists):
        logger.info(f"  - {playlist}")
    
    logger.info("\nRetrying failed playlists...")
    
    # Initialize sync service
    sync_service = SyncService(credentials_path=credentials_path)
    
    # Load credentials and authenticate
    try:
        credentials = sync_service.load_credentials()
        if not credentials:
            logger.error("Failed to load credentials")
            return
        
        sync_service.authenticate_clients(credentials)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return
    
    # Get all playlists
    all_playlists = sync_service.spotify_client.list_playlists()
    
    # Filter to only the failed ones
    playlists_to_retry = [
        p for p in all_playlists 
        if p['name'] in failed_playlists
    ]
    
    if not playlists_to_retry:
        logger.warning("Could not find any of the failed playlists in Spotify")
        logger.warning(f"Failed playlist names: {failed_playlists}")
        return
    
    logger.info(f"\nRetrying {len(playlists_to_retry)} playlists...")
    
    # Retry each playlist
    success_count = 0
    for i, playlist in enumerate(playlists_to_retry, 1):
        logger.info(f"\nRetrying playlist {i}/{len(playlists_to_retry)}")
        result = sync_service.sync_playlist(
            playlist,
            dry_run=dry_run,
            update_existing=True
        )
        if result:
            success_count += 1
    
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Retry Summary:")
    logger.info(f"  Total playlists retried: {len(playlists_to_retry)}")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {len(playlists_to_retry) - success_count}")
    logger.info(f"{'=' * 60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Retry failed playlist syncs from log file"
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file to analyze (default: latest in sync_logs/)",
        default=None
    )
    parser.add_argument(
        "--dry-run",
        type=lambda x: x.lower() == 'true',
        default=True,
        help="Run in dry-run mode (true/false, default: true)"
    )
    parser.add_argument(
        "--credentials",
        default="credentials.md",
        help="Path to credentials file (default: credentials.md)"
    )
    
    args = parser.parse_args()
    
    try:
        # Get log file to analyze
        if args.log_file:
            log_path = Path(args.log_file)
        else:
            log_path = get_latest_log_file()
        
        logger.info(f"Analyzing log file: {log_path}")
        logger.info(f"Log file size: {log_path.stat().st_size:,} bytes")
        logger.info(f"Last modified: {log_path.stat().st_mtime}")
        
        # Parse log file to find failed playlists
        failed_playlists = parse_log_file(str(log_path))
        
        # Retry failed playlists
        retry_failed_playlists(
            failed_playlists,
            dry_run=args.dry_run,
            credentials_path=args.credentials
        )
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nRetry interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
