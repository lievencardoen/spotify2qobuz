"""
Qobuz API client using token-based authentication.

This approach uses session tokens from browser cookies instead of app_id/password,
which works with Google login accounts and bypasses 2025 API restrictions.
"""

from typing import Dict, List, Optional
import requests
from src.utils.logger import get_logger


logger = get_logger()


class QobuzClient:
    """
    Client for interacting with Qobuz API using session token authentication.
    
    Get your token from browser cookies after logging in to https://play.qobuz.com
    See GET_TOKEN_INSTRUCTIONS.md for detailed instructions.
    """
    
    BASE_URL = "https://www.qobuz.com/api.json/0.2"
    
    def __init__(self, user_auth_token: str):
        """
        Initialize Qobuz client with session token.
        
        Args:
            user_auth_token: Session token from browser cookies (user_auth_token or X-User-Auth-Token)
        """
        self.user_auth_token = user_auth_token
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None
        
        # Create session with required headers
        self._session = requests.Session()
        self._session.headers.update({
            "X-App-Id": "798273057",  # App ID used by web player
            "X-User-Auth-Token": self.user_auth_token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://play.qobuz.com",
            "Referer": "https://play.qobuz.com/",
        })
    
    def authenticate(self) -> None:
        """
        Validate the session token by fetching user favorites (doesn't require app_id).
        
        Raises:
            Exception: If token is invalid or expired
        """
        try:
            # Use an endpoint that works with just the token (no app_id needed)
            # Try to get user favorites which validates the token
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {"type": "albums", "limit": 1}
            
            response = self._session.get(url, params=params, timeout=10)
            
            if response.status_code == 401 or response.status_code == 400:
                logger.error(f"Token validation failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                logger.info("Your token may be expired. Please get a fresh one from:")
                logger.info("https://play.qobuz.com → DevTools → Application → Cookies → qobuz.com")
                logger.info("See GET_TOKEN_INSTRUCTIONS.md for help")
                raise Exception(f"Invalid or expired Qobuz token (status {response.status_code})")
            
            # If we got here, the token works!
            # Extract user info from the response if available
            data = response.json()
            
            # Try to get user ID from the response
            if 'user' in data and 'id' in data['user']:
                self.user_id = data['user']['id']
                self.user_name = data['user'].get('display_name', 'Qobuz User')
            else:
                # If user info not in this response, set defaults
                # The token is valid, we just don't have the user details yet
                self.user_id = 1  # Placeholder
                self.user_name = "Qobuz User"
            
            logger.info(f"✅ Authenticated with Qobuz successfully")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during token validation: {e}")
            raise Exception(f"Qobuz authentication failed: {e}")
    
    def _make_request(self, endpoint: str, params: Dict = None, method: str = "GET") -> Dict:
        """
        Make authenticated request to Qobuz API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters or request body
            method: HTTP method (GET or POST)
        
        Returns:
            Response JSON
        
        Raises:
            Exception: If request fails
        """
        if not self.user_auth_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=10)
            else:  # POST
                response = self._session.post(url, json=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Qobuz API request failed for {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Qobuz API request failed: {e}")
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        """
        Search for a track by ISRC code.
        
        Args:
            isrc: ISRC code
        
        Returns:
            Track dictionary with keys: id, title, artist, album, duration
            or None if not found
        """
        try:
            params = {
                'query': isrc,
                'limit': 5
            }
            
            data = self._make_request('track/search', params)
            
            if data.get('tracks', {}).get('total', 0) == 0:
                logger.debug(f"No track found for ISRC: {isrc}")
                return None
            
            # Find exact ISRC match
            for item in data['tracks']['items']:
                track_isrc = item.get('isrc')
                if track_isrc and track_isrc.upper() == isrc.upper():
                    track = {
                        'id': item['id'],
                        'title': item['title'],
                        'artist': item['performer']['name'],
                        'album': item['album']['title'],
                        'duration': item['duration'] * 1000  # Convert to milliseconds
                    }
                    logger.debug(f"Found track by ISRC {isrc}: {track['title']} by {track['artist']}")
                    return track
            
            logger.debug(f"No exact ISRC match found for: {isrc}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching by ISRC {isrc}: {e}")
            return None
    
    def search_by_metadata(self, title: str, artist: str, duration: int) -> Optional[Dict]:
        """
        Search for a track by metadata (title, artist, duration).
        
        Args:
            title: Track title
            artist: Artist name
            duration: Duration in milliseconds
        
        Returns:
            Track dictionary with keys: id, title, artist, album, duration
            or None if not found
        """
        try:
            query = f"{title} {artist}"
            params = {
                'query': query,
                'limit': 10
            }
            
            data = self._make_request('track/search', params)
            
            if data.get('tracks', {}).get('total', 0) == 0:
                logger.debug(f"No tracks found for query: {query}")
                return None
            
            # Return first result (fuzzy matching will be done by matcher.py)
            items = data['tracks']['items']
            if items:
                item = items[0]
                track = {
                    'id': item['id'],
                    'title': item['title'],
                    'artist': item['performer']['name'],
                    'album': item['album']['title'],
                    'duration': item['duration'] * 1000  # Convert to milliseconds
                }
                logger.debug(f"Found track by metadata: {track['title']} by {track['artist']}")
                return track
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching by metadata {title} - {artist}: {e}")
            return None
    
    def create_playlist(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
        
        Returns:
            Playlist ID or None if creation fails
        """
        try:
            url = f"{self.BASE_URL}/playlist/create"
            
            # Use form data instead of query params to handle special characters
            data = {
                'name': name,
                'is_public': 'false',
                'is_collaborative': 'false'
            }
            
            if description:
                data['description'] = description
            
            # POST with form data
            response = self._session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            playlist_id = str(result['id'])
            
            logger.info(f"Created Qobuz playlist: {name} (ID: {playlist_id})")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error creating playlist {name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def add_track(self, playlist_id: str, track_id: int) -> bool:
        """
        Add a track to a playlist.
        
        Args:
            playlist_id: Playlist ID
            track_id: Track ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/playlist/addTracks"
            
            # Use form data for POST
            data = {
                'playlist_id': playlist_id,
                'track_ids': str(track_id)
            }
            
            response = self._session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.debug(f"Added track {track_id} to playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding track {track_id} to playlist {playlist_id}: {e}")
            return False
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        Get playlist details.
        
        Args:
            playlist_id: Playlist ID
        
        Returns:
            Playlist data or None if not found
        """
        try:
            params = {'playlist_id': playlist_id}
            data = self._make_request('playlist/get', params)
            return data
        except Exception as e:
            logger.error(f"Error getting playlist {playlist_id}: {e}")
            return None
    
    def list_user_playlists(self) -> List[Dict]:
        """
        Get all user playlists.
        
        Returns:
            List of playlist dictionaries with keys: id, name, tracks_count
        """
        try:
            params = {'limit': 500}  # Get up to 500 playlists
            data = self._make_request('playlist/getUserPlaylists', params)
            
            playlists = []
            if data.get('playlists', {}).get('items'):
                for item in data['playlists']['items']:
                    playlists.append({
                        'id': str(item['id']),
                        'name': item['name'],
                        'tracks_count': item.get('tracks_count', 0)
                    })
                    
            logger.info(f"Found {len(playlists)} Qobuz playlists")
            return playlists
            
        except Exception as e:
            logger.error(f"Error listing user playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str) -> List[int]:
        """
        Get all track IDs in a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            List of track IDs
        """
        try:
            playlist_data = self.get_playlist(playlist_id)
            if not playlist_data or 'tracks' not in playlist_data:
                return []
            
            track_ids = []
            if 'items' in playlist_data['tracks']:
                track_ids = [track['id'] for track in playlist_data['tracks']['items']]
            
            logger.debug(f"Found {len(track_ids)} tracks in playlist {playlist_id}")
            return track_ids
            
        except Exception as e:
            logger.error(f"Error getting playlist tracks {playlist_id}: {e}")
            return []
    
    def find_playlist_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a playlist by exact name match.
        
        Args:
            name: Playlist name to search for
            
        Returns:
            Playlist dict with keys: id, name, tracks_count, or None if not found
        """
        playlists = self.list_user_playlists()
        for playlist in playlists:
            if playlist['name'] == name:
                logger.debug(f"Found existing playlist: {name} (ID: {playlist['id']})")
                return playlist
        return None
    
    def get_favorite_tracks(self, limit: int = 5000) -> List[int]:
        """
        Get all favorite/liked track IDs for the authenticated user.
        
        Args:
            limit: Maximum number of favorites to retrieve (default: 5000)
        
        Returns:
            List of track IDs that are favorited
        
        Raises:
            Exception: If API call fails
        """
        try:
            url = f"{self.BASE_URL}/favorite/getUserFavorites"
            params = {
                "type": "tracks",
                "limit": limit,
                "offset": 0
            }
            
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            track_ids = []
            
            if 'tracks' in data and 'items' in data['tracks']:
                for item in data['tracks']['items']:
                    if 'id' in item:
                        track_ids.append(item['id'])
            
            logger.info(f"Retrieved {len(track_ids)} favorite tracks from Qobuz")
            return track_ids
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get favorite tracks: {e}")
            raise Exception(f"Failed to get favorite tracks: {e}")
    
    def add_favorite_track(self, track_id: int) -> bool:
        """
        Add a track to user's favorites.
        
        Args:
            track_id: Qobuz track ID to favorite
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            Exception: If API call fails
        """
        try:
            url = f"{self.BASE_URL}/favorite/create"
            params = {
                "track_ids": str(track_id)
            }
            
            response = self._session.post(url, params=params, timeout=10)
            
            # Qobuz may return 400 if already favorited, which is fine
            if response.status_code == 400:
                logger.debug(f"Track {track_id} is already favorited")
                return True
            
            response.raise_for_status()
            logger.debug(f"Added track {track_id} to favorites")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add track {track_id} to favorites: {e}")
            return False
    
    def is_track_favorited(self, track_id: int) -> bool:
        """
        Check if a track is in user's favorites.
        
        Args:
            track_id: Qobuz track ID to check
        
        Returns:
            True if track is favorited, False otherwise
        """
        try:
            favorites = self.get_favorite_tracks()
            return track_id in favorites
        except Exception:
            return False
