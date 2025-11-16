"""Track matching logic using ISRC and fuzzy matching."""

from typing import Dict, Optional, Tuple
from rapidfuzz import fuzz
from src.qobuz_client import QobuzClient
from src.utils.logger import get_logger


logger = get_logger()


class MatchResult:
    """Result of a track matching operation."""
    
    def __init__(
        self,
        qobuz_track: Dict,
        match_type: str,
        score: float
    ):
        """
        Initialize match result.
        
        Args:
            qobuz_track: Qobuz track dictionary
            match_type: Type of match ('isrc' or 'fuzzy')
            score: Match confidence score (0-100)
        """
        self.qobuz_track = qobuz_track
        self.match_type = match_type
        self.score = score
    
    def __repr__(self) -> str:
        return f"MatchResult(type={self.match_type}, score={self.score:.2f})"


class TrackMatcher:
    """Matcher for finding Qobuz tracks that correspond to Spotify tracks."""
    
    # Thresholds for fuzzy matching
    TITLE_THRESHOLD = 80
    ARTIST_THRESHOLD = 75
    DURATION_TOLERANCE_MS = 5000  # 5 seconds
    MIN_COMBINED_SCORE = 75
    
    def __init__(self, qobuz_client: QobuzClient):
        """
        Initialize track matcher.
        
        Args:
            qobuz_client: Authenticated Qobuz client
        """
        self.qobuz_client = qobuz_client
    
    def match_track(self, spotify_track: Dict) -> Optional[MatchResult]:
        """
        Match a Spotify track to a Qobuz track.
        
        Strategy:
        1. Try ISRC matching first (if ISRC is available)
        2. Fall back to fuzzy matching using title, artist, and duration
        
        Args:
            spotify_track: Spotify track dictionary with keys:
                          title, artist, album, duration, isrc
        
        Returns:
            MatchResult if a match is found, None otherwise
        """
        # Try ISRC matching first
        if spotify_track.get('isrc'):
            result = self._match_by_isrc(spotify_track)
            if result:
                return result
        
        # Fall back to fuzzy matching
        return self._match_by_fuzzy(spotify_track)
    
    def _match_by_isrc(self, spotify_track: Dict) -> Optional[MatchResult]:
        """
        Match track using ISRC code.
        
        Args:
            spotify_track: Spotify track dictionary
        
        Returns:
            MatchResult with match_type='isrc' if found, None otherwise
        """
        isrc = spotify_track['isrc']
        qobuz_track = self.qobuz_client.search_by_isrc(isrc)
        
        if qobuz_track:
            logger.info(
                f"ISRC match: {spotify_track['title']} by {spotify_track['artist']} "
                f"-> {qobuz_track['title']} by {qobuz_track['artist']}"
            )
            return MatchResult(
                qobuz_track=qobuz_track,
                match_type='isrc',
                score=100.0
            )
        
        return None
    
    def _match_by_fuzzy(self, spotify_track: Dict) -> Optional[MatchResult]:
        """
        Match track using fuzzy string matching.
        
        Args:
            spotify_track: Spotify track dictionary
        
        Returns:
            MatchResult with match_type='fuzzy' if match score is high enough,
            None otherwise
        """
        qobuz_track = self.qobuz_client.search_by_metadata(
            spotify_track['title'],
            spotify_track['artist'],
            spotify_track['duration']
        )
        
        if not qobuz_track:
            return None
        
        # Calculate fuzzy match scores
        title_score = fuzz.ratio(
            self._normalize_string(spotify_track['title']),
            self._normalize_string(qobuz_track['title'])
        )
        
        artist_score = fuzz.ratio(
            self._normalize_string(spotify_track['artist']),
            self._normalize_string(qobuz_track['artist'])
        )
        
        # Check duration proximity
        duration_diff = abs(spotify_track['duration'] - qobuz_track['duration'])
        duration_match = duration_diff <= self.DURATION_TOLERANCE_MS
        
        # Calculate combined score
        combined_score = (title_score * 0.6) + (artist_score * 0.4)
        
        # Check if match meets thresholds
        if (title_score >= self.TITLE_THRESHOLD and
            artist_score >= self.ARTIST_THRESHOLD and
            duration_match and
            combined_score >= self.MIN_COMBINED_SCORE):
            
            logger.info(
                f"Fuzzy match (score={combined_score:.2f}): "
                f"{spotify_track['title']} by {spotify_track['artist']} "
                f"-> {qobuz_track['title']} by {qobuz_track['artist']}"
            )
            
            return MatchResult(
                qobuz_track=qobuz_track,
                match_type='fuzzy',
                score=combined_score
            )
        
        logger.debug(
            f"No fuzzy match (scores: title={title_score:.2f}, "
            f"artist={artist_score:.2f}, combined={combined_score:.2f}, "
            f"duration_match={duration_match}): "
            f"{spotify_track['title']} by {spotify_track['artist']}"
        )
        
        return None
    
    @staticmethod
    def _normalize_string(s: str) -> str:
        """
        Normalize string for comparison.
        
        Args:
            s: Input string
        
        Returns:
            Normalized string (lowercase, stripped)
        """
        return s.lower().strip()


def find_best_match(spotify_track: Dict, search_results: list) -> Optional[Dict]:
    """
    Find the best matching track from search results.
    
    This is a simplified version for favorite syncing that doesn't require
    a full TrackMatcher instance. It uses fuzzy matching to find the best result.
    
    Args:
        spotify_track: Normalized Spotify track with keys: title, artist, album, duration
        search_results: List of Qobuz track dictionaries from search
    
    Returns:
        Best matching Qobuz track dict, or None if no good match found
    """
    if not search_results:
        return None
    
    best_match = None
    best_score = 0
    
    spotify_title = spotify_track['title'].lower().strip()
    spotify_artist = spotify_track['artist'].lower().strip()
    
    for qobuz_track in search_results:
        qobuz_title = qobuz_track.get('title', '').lower().strip()
        qobuz_artist = qobuz_track.get('performer', {}).get('name', '').lower().strip()
        
        # Calculate fuzzy match scores
        title_score = fuzz.ratio(spotify_title, qobuz_title)
        artist_score = fuzz.ratio(spotify_artist, qobuz_artist)
        
        # Combined score (weighted: title 60%, artist 40%)
        combined_score = (title_score * 0.6) + (artist_score * 0.4)
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = qobuz_track
    
    # Only return match if score is above threshold (70%)
    if best_score >= 70:
        return best_match
    
    return None
