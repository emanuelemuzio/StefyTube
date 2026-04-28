"""Unit tests for src/requests.py - API request models."""

import pytest
from src.requests import (
    DownloadRequest,
    HistoryDeleteRequest,
    QueueDeleteRequest,
    MergeDeleteRequest,
    MergeUuidList
)


class TestDownloadRequest:
    """Tests for DownloadRequest model."""

    def test_download_request_required_fields(self):
        """Test DownloadRequest can be created with required fields."""
        req = DownloadRequest(
            url='https://youtube.com/watch?v=test',
            format='mp3',
            noplaylist=True
        )
        assert req.url == 'https://youtube.com/watch?v=test'
        assert req.format == 'mp3'
        assert req.noplaylist is True

    def test_download_request_mp4(self):
        """Test DownloadRequest with mp4 format."""
        req = DownloadRequest(
            url='https://youtube.com/watch?v=test',
            format='mp4',
            noplaylist=False
        )
        assert req.format == 'mp4'
        assert req.noplaylist is False

    def test_download_request_missing_url(self):
        """Test DownloadRequest validation fails without URL."""
        with pytest.raises(ValueError):
            DownloadRequest(format='mp3', noplaylist=True)


class TestDeleteRequests:
    """Tests for delete request models."""

    def test_history_delete_request(self):
        """Test HistoryDeleteRequest."""
        req = HistoryDeleteRequest(uuid='test-uuid-123')
        assert req.uuid == 'test-uuid-123'

    def test_queue_delete_request(self):
        """Test QueueDeleteRequest."""
        req = QueueDeleteRequest(uuid='test-uuid-456')
        assert req.uuid == 'test-uuid-456'

    def test_merge_delete_request(self):
        """Test MergeDeleteRequest."""
        req = MergeDeleteRequest(uuid='test-uuid-789')
        assert req.uuid == 'test-uuid-789'


class TestMergeUuidList:
    """Tests for MergeUuidList request model."""

    def test_merge_uuid_list_required_fields(self):
        """Test MergeUuidList can be created with required fields."""
        req = MergeUuidList(
            uuids=['uuid1', 'uuid2', 'uuid3'],
            title='My Playlist'
        )
        assert req.uuids == ['uuid1', 'uuid2', 'uuid3']
        assert req.title == 'My Playlist'
        assert len(req.uuids) == 3

    def test_merge_uuid_list_empty_title(self):
        """Test MergeUuidList with empty title (Pydantic allows empty strings by default)."""
        # Note: Pydantic 2.x allows empty strings by default
        req = MergeUuidList(uuids=['uuid1', 'uuid2'], title='')
        assert req.title == ''

    def test_merge_uuid_list_single_uuid(self):
        """Test MergeUuidList with single UUID."""
        req = MergeUuidList(uuids=['only-one'], title='Single Track')
        assert len(req.uuids) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
