"""Spotify API client for retrieving playlists and tracks."""

from typing import Dict, List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.utils.logger import get_logger


logger = get_logger()


class SpotifyClient:
    """Client for interacting with Spotify Web API."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Spotify client.
        
        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp: Optional[spotipy.Spotify] = None
    
    def authenticate_user(self) -> None:
        """
        Authenticate user with Spotify using OAuth.
        
        Raises:
            Exception: If authentication fails
        """
        try:
            scope = "playlist-read-private playlist-read-collaborative user-library-read"
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication
            user = self.sp.current_user()
            logger.info(f"Authenticated as Spotify user: {user['display_name']}")
            
        except Exception as e:
            logger.error(f"Spotify authentication failed: {e}")
            raise
    
    def list_playlists(self) -> List[Dict]:
        """
        List all playlists for the authenticated user.
        
        Returns:
            List of playlist dictionaries with keys: id, name, tracks_count
        
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate_user() first.")
        
        playlists = []
        offset = 0
        limit = 50
        
        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            
            for item in results['items']:
                playlist = {
                    'id': item['id'],
                    'name': item['name'],
                    'tracks_count': item['tracks']['total']
                }
                playlists.append(playlist)
                logger.debug(f"Found playlist: {playlist['name']} ({playlist['tracks_count']} tracks)")
            
            if not results['next']:
                break
            
            offset += limit
        
        logger.info(f"Retrieved {len(playlists)} playlists from Spotify")
        return playlists
    
    def list_tracks(self, playlist_id: str) -> List[Dict]:
        """
        List all tracks in a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
        
        Returns:
            List of normalized track dictionaries with keys:
            - title: Track title
            - artist: Primary artist name
            - album: Album name
            - duration: Duration in milliseconds
            - isrc: ISRC code (if available)
        
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate_user() first.")
        
        tracks = []
        offset = 0
        limit = 100
        
        while True:
            results = self.sp.playlist_tracks(
                playlist_id,
                offset=offset,
                limit=limit,
                fields='items(track(name,artists,album,duration_ms,external_ids)),next'
            )
            
            for item in results['items']:
                track_data = item.get('track')
                if not track_data:
                    continue
                
                # Extract ISRC if available
                isrc = None
                external_ids = track_data.get('external_ids', {})
                if external_ids and 'isrc' in external_ids:
                    isrc = external_ids['isrc']
                
                # Get primary artist
                artist = track_data['artists'][0]['name'] if track_data['artists'] else "Unknown"
                
                track = {
                    'title': track_data['name'],
                    'artist': artist,
                    'album': track_data['album']['name'],
                    'duration': track_data['duration_ms'],
                    'isrc': isrc
                }
                tracks.append(track)
            
            if not results['next']:
                break
            
            offset += limit
        
        logger.info(f"Retrieved {len(tracks)} tracks from playlist {playlist_id}")
        return tracks
    
    def get_saved_tracks(self) -> List[Dict]:
        """
        Get all saved/liked tracks for the authenticated user.
        
        Returns:
            List of normalized track dictionaries with keys:
            - title: Track title
            - artist: Primary artist name
            - album: Album name
            - duration: Duration in milliseconds
            - isrc: ISRC code (if available)
        
        Raises:
            Exception: If not authenticated or API call fails
        """
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate_user() first.")
        
        tracks = []
        offset = 0
        limit = 50
        
        while True:
            results = self.sp.current_user_saved_tracks(
                limit=limit,
                offset=offset
            )
            
            for item in results['items']:
                track_data = item.get('track')
                if not track_data:
                    continue
                
                # Extract ISRC if available
                isrc = None
                external_ids = track_data.get('external_ids', {})
                if external_ids and 'isrc' in external_ids:
                    isrc = external_ids['isrc']
                
                # Get primary artist
                artist = track_data['artists'][0]['name'] if track_data['artists'] else "Unknown"
                
                track = {
                    'title': track_data['name'],
                    'artist': artist,
                    'album': track_data['album']['name'],
                    'duration': track_data['duration_ms'],
                    'isrc': isrc
                }
                tracks.append(track)
            
            if not results['next']:
                break
            
            offset += limit
        
        logger.info(f"Retrieved {len(tracks)} saved tracks from Spotify")
        return tracks
