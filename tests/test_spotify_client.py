"""Unit tests for Spotify client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.spotify_client import SpotifyClient


@pytest.fixture
def spotify_client():
    """Create a Spotify client instance."""
    return SpotifyClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8888/callback"
    )


@pytest.fixture
def mock_spotify():
    """Create a mock Spotify API object."""
    mock = Mock()
    mock.current_user.return_value = {'display_name': 'Test User'}
    return mock


class TestSpotifyClient:
    """Test cases for SpotifyClient."""
    
    def test_init(self, spotify_client):
        """Test client initialization."""
        assert spotify_client.client_id == "test_client_id"
        assert spotify_client.client_secret == "test_client_secret"
        assert spotify_client.redirect_uri == "http://localhost:8888/callback"
        assert spotify_client.sp is None
    
    @patch('src.spotify_client.spotipy.Spotify')
    @patch('src.spotify_client.SpotifyOAuth')
    def test_authenticate_user_success(self, mock_oauth, mock_spotify_class, spotify_client):
        """Test successful user authentication."""
        mock_sp = Mock()
        mock_sp.current_user.return_value = {'display_name': 'Test User'}
        mock_spotify_class.return_value = mock_sp
        
        spotify_client.authenticate_user()
        
        assert spotify_client.sp == mock_sp
        mock_oauth.assert_called_once()
        mock_sp.current_user.assert_called_once()
    
    @patch('src.spotify_client.spotipy.Spotify')
    @patch('src.spotify_client.SpotifyOAuth')
    def test_authenticate_user_failure(self, mock_oauth, mock_spotify_class, spotify_client):
        """Test authentication failure."""
        mock_spotify_class.side_effect = Exception("Auth failed")
        
        with pytest.raises(Exception, match="Auth failed"):
            spotify_client.authenticate_user()
    
    def test_list_playlists_not_authenticated(self, spotify_client):
        """Test listing playlists without authentication."""
        with pytest.raises(Exception, match="Not authenticated"):
            spotify_client.list_playlists()
    
    def test_list_playlists_single_page(self, spotify_client, mock_spotify):
        """Test listing playlists with single page of results."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_playlists.return_value = {
            'items': [
                {'id': 'p1', 'name': 'Playlist 1', 'tracks': {'total': 10}},
                {'id': 'p2', 'name': 'Playlist 2', 'tracks': {'total': 20}}
            ],
            'next': None
        }
        
        playlists = spotify_client.list_playlists()
        
        assert len(playlists) == 2
        assert playlists[0]['id'] == 'p1'
        assert playlists[0]['name'] == 'Playlist 1'
        assert playlists[0]['tracks_count'] == 10
        assert playlists[1]['id'] == 'p2'
        assert playlists[1]['name'] == 'Playlist 2'
        assert playlists[1]['tracks_count'] == 20
    
    def test_list_playlists_multiple_pages(self, spotify_client, mock_spotify):
        """Test listing playlists with pagination."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_playlists.side_effect = [
            {
                'items': [
                    {'id': 'p1', 'name': 'Playlist 1', 'tracks': {'total': 10}}
                ],
                'next': 'next_page_url'
            },
            {
                'items': [
                    {'id': 'p2', 'name': 'Playlist 2', 'tracks': {'total': 20}}
                ],
                'next': None
            }
        ]
        
        playlists = spotify_client.list_playlists()
        
        assert len(playlists) == 2
        assert mock_spotify.current_user_playlists.call_count == 2
    
    def test_list_tracks_not_authenticated(self, spotify_client):
        """Test listing tracks without authentication."""
        with pytest.raises(Exception, match="Not authenticated"):
            spotify_client.list_tracks('playlist_id')
    
    def test_list_tracks_with_isrc(self, spotify_client, mock_spotify):
        """Test listing tracks with ISRC codes."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.playlist_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Track 1',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {'name': 'Album 1'},
                        'duration_ms': 180000,
                        'external_ids': {'isrc': 'USRC17607839'}
                    }
                }
            ],
            'next': None
        }
        
        tracks = spotify_client.list_tracks('playlist_id')
        
        assert len(tracks) == 1
        assert tracks[0]['title'] == 'Track 1'
        assert tracks[0]['artist'] == 'Artist 1'
        assert tracks[0]['album'] == 'Album 1'
        assert tracks[0]['duration'] == 180000
        assert tracks[0]['isrc'] == 'USRC17607839'
    
    def test_list_tracks_without_isrc(self, spotify_client, mock_spotify):
        """Test listing tracks without ISRC codes."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.playlist_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Track 1',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {'name': 'Album 1'},
                        'duration_ms': 180000,
                        'external_ids': {}
                    }
                }
            ],
            'next': None
        }
        
        tracks = spotify_client.list_tracks('playlist_id')
        
        assert len(tracks) == 1
        assert tracks[0]['isrc'] is None
    
    def test_list_tracks_skip_null_tracks(self, spotify_client, mock_spotify):
        """Test that null tracks are skipped."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.playlist_tracks.return_value = {
            'items': [
                {'track': None},
                {
                    'track': {
                        'name': 'Track 1',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {'name': 'Album 1'},
                        'duration_ms': 180000,
                        'external_ids': {}
                    }
                }
            ],
            'next': None
        }
        
        tracks = spotify_client.list_tracks('playlist_id')
        
        assert len(tracks) == 1
        assert tracks[0]['title'] == 'Track 1'
    
    def test_list_tracks_pagination(self, spotify_client, mock_spotify):
        """Test listing tracks with pagination."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.playlist_tracks.side_effect = [
            {
                'items': [
                    {
                        'track': {
                            'name': 'Track 1',
                            'artists': [{'name': 'Artist 1'}],
                            'album': {'name': 'Album 1'},
                            'duration_ms': 180000,
                            'external_ids': {}
                        }
                    }
                ],
                'next': 'next_page'
            },
            {
                'items': [
                    {
                        'track': {
                            'name': 'Track 2',
                            'artists': [{'name': 'Artist 2'}],
                            'album': {'name': 'Album 2'},
                            'duration_ms': 200000,
                            'external_ids': {}
                        }
                    }
                ],
                'next': None
            }
        ]
        
        tracks = spotify_client.list_tracks('playlist_id')
        
        assert len(tracks) == 2
        assert mock_spotify.playlist_tracks.call_count == 2
    
    def test_get_saved_tracks_not_authenticated(self, spotify_client):
        """Test getting saved tracks when not authenticated."""
        with pytest.raises(Exception, match="Not authenticated"):
            spotify_client.get_saved_tracks()
    
    def test_get_saved_tracks_success(self, spotify_client, mock_spotify):
        """Test getting saved tracks successfully."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_saved_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Saved Track 1',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {'name': 'Album 1'},
                        'duration_ms': 200000,
                        'external_ids': {'isrc': 'SAVED001'}
                    }
                },
                {
                    'track': {
                        'name': 'Saved Track 2',
                        'artists': [{'name': 'Artist 2'}],
                        'album': {'name': 'Album 2'},
                        'duration_ms': 180000,
                        'external_ids': {}
                    }
                }
            ],
            'next': None
        }
        
        tracks = spotify_client.get_saved_tracks()
        
        assert len(tracks) == 2
        assert tracks[0]['title'] == 'Saved Track 1'
        assert tracks[0]['artist'] == 'Artist 1'
        assert tracks[0]['album'] == 'Album 1'
        assert tracks[0]['duration'] == 200000
        assert tracks[0]['isrc'] == 'SAVED001'
        
        assert tracks[1]['title'] == 'Saved Track 2'
        assert tracks[1]['isrc'] is None
        
        mock_spotify.current_user_saved_tracks.assert_called_once_with(
            limit=50,
            offset=0
        )
    
    def test_get_saved_tracks_pagination(self, spotify_client, mock_spotify):
        """Test getting saved tracks with pagination."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_saved_tracks.side_effect = [
            {
                'items': [
                    {
                        'track': {
                            'name': 'Track 1',
                            'artists': [{'name': 'Artist 1'}],
                            'album': {'name': 'Album 1'},
                            'duration_ms': 200000,
                            'external_ids': {}
                        }
                    }
                ],
                'next': 'next_url'
            },
            {
                'items': [
                    {
                        'track': {
                            'name': 'Track 2',
                            'artists': [{'name': 'Artist 2'}],
                            'album': {'name': 'Album 2'},
                            'duration_ms': 180000,
                            'external_ids': {}
                        }
                    }
                ],
                'next': None
            }
        ]
        
        tracks = spotify_client.get_saved_tracks()
        
        assert len(tracks) == 2
        assert mock_spotify.current_user_saved_tracks.call_count == 2
    
    def test_get_saved_tracks_empty(self, spotify_client, mock_spotify):
        """Test getting saved tracks when user has none."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_saved_tracks.return_value = {
            'items': [],
            'next': None
        }
        
        tracks = spotify_client.get_saved_tracks()
        
        assert len(tracks) == 0
    
    def test_get_saved_tracks_missing_track_data(self, spotify_client, mock_spotify):
        """Test getting saved tracks when some items have no track data."""
        spotify_client.sp = mock_spotify
        
        mock_spotify.current_user_saved_tracks.return_value = {
            'items': [
                {'track': None},  # Missing track data
                {
                    'track': {
                        'name': 'Valid Track',
                        'artists': [{'name': 'Artist'}],
                        'album': {'name': 'Album'},
                        'duration_ms': 200000,
                        'external_ids': {}
                    }
                }
            ],
            'next': None
        }
        
        tracks = spotify_client.get_saved_tracks()
        
        assert len(tracks) == 1
        assert tracks[0]['title'] == 'Valid Track'
