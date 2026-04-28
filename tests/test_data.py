"""Unit tests for src/data.py - Entry, Merge, and Data models."""

import os
import tempfile
import pytest
from src.data import Entry, Merge, Data


class TestEntry:
    """Tests for Entry model."""
    
    def test_entry_creation(self):
        """Test Entry can be created with required fields."""
        entry = Entry(url='https://youtube.com/watch?v=test')
        assert entry.url == 'https://youtube.com/watch?v=test'
        assert entry.format == 'mp3'  # Default
        assert entry.status == 'queued'  # Default
        assert entry.uuid is not None
        assert len(entry.uuid) > 0
    
    def test_entry_with_all_fields(self):
        """Test Entry with all fields specified."""
        entry = Entry(
            id='vid123',
            url='https://youtube.com/watch?v=test',
            title='Test Video',
            format='mp4',
            status='downloading',
            progress=50
        )
        assert entry.id == 'vid123'
        assert entry.title == 'Test Video'
        assert entry.format == 'mp4'
        assert entry.status == 'downloading'
        assert entry.progress == 50
    
    def test_entry_serialize(self):
        """Test Entry serialization to dict."""
        entry = Entry(
            url='https://youtube.com/watch?v=test',
            title='Test',
            format='mp3'
        )
        serialized = entry.serialize()
        assert isinstance(serialized, dict)
        assert serialized['url'] == 'https://youtube.com/watch?v=test'
        assert serialized['title'] == 'Test'
        assert serialized['format'] == 'mp3'
    
    def test_entry_uuid_unique(self):
        """Test each Entry gets unique UUID."""
        entry1 = Entry(url='https://youtube.com/watch?v=test1')
        entry2 = Entry(url='https://youtube.com/watch?v=test2')
        assert entry1.uuid != entry2.uuid


class TestMerge:
    """Tests for Merge model."""
    
    def test_merge_creation(self):
        """Test Merge can be created."""
        merge = Merge(title='My Playlist', format='mp3')
        assert merge.title == 'My Playlist'
        assert merge.format == 'mp3'
        assert merge.uuid is not None
    
    def test_merge_serialize(self):
        """Test Merge serialization."""
        merge = Merge(title='Test Merge', format='mp3', filepath='/path/to/file')
        serialized = merge.serialize()
        assert serialized['title'] == 'Test Merge'
        assert serialized['format'] == 'mp3'
        assert serialized['filepath'] == '/path/to/file'


class TestData:
    """Tests for Data model and methods."""
    
    def test_data_creation(self):
        """Test Data object creation."""
        data = Data()
        assert isinstance(data.queue, list)
        assert isinstance(data.history, list)
        assert isinstance(data.merge, list)
        assert len(data.queue) == 0
    
    def test_add_to_queue(self, sample_entry):
        """Test adding entry to queue."""
        data = Data()
        data.add_to_queue(sample_entry)
        assert len(data.queue) == 1
        assert data.queue[0] == sample_entry
    
    def test_add_to_merge(self):
        """Test adding merge to list."""
        data = Data()
        merge = Merge(title='Test', format='mp3')
        data.add_to_merge(merge)
        assert len(data.merge) == 1
        assert data.merge[0] == merge
    
    def test_move_to_history_with_uuid(self, sample_entry, sample_entry_mp4):
        """Test move_to_history uses UUID-based removal (bug fix #6)."""
        data = Data()
        data.add_to_queue(sample_entry)
        data.add_to_queue(sample_entry_mp4)

        # Both have different UUIDs
        assert sample_entry.uuid != sample_entry_mp4.uuid

        # Move only first entry to history
        data.move_to_history(sample_entry)

        # Should only remove the specific entry, not all entries
        assert len(data.queue) == 1
        assert data.queue[0].uuid == sample_entry_mp4.uuid
        assert len(data.history) == 1
        assert data.history[0].uuid == sample_entry.uuid
    
    def test_should_download_duplicate(self, sample_entry):
        """Test should_download detects duplicates."""
        data = Data()
        entry = Entry(url=sample_entry.url, format=sample_entry.format, status='completed')
        data.history.append(entry)
        
        # Same URL, same format, completed in history -> should NOT download
        assert data.should_download(sample_entry) == False
    
    def test_should_download_different_format(self, sample_entry, sample_entry_mp4):
        """Test should_download allows different formats (bug fix)."""
        data = Data()
        mp3_entry = Entry(
            url=sample_entry.url,
            format='mp3',
            status='completed'
        )
        data.history.append(mp3_entry)
        
        # Same URL but different format -> should download
        mp4_entry = Entry(url=sample_entry.url, format='mp4')
        assert data.should_download(mp4_entry) == True
    
    def test_get_history_entry_by_uuid(self, sample_entry):
        """Test retrieving entry from history by UUID."""
        data = Data()
        completed_entry = Entry(url=sample_entry.url, status='completed')
        data.history.append(completed_entry)
        
        retrieved = data.get_history_entry_by_uuid(completed_entry.uuid)
        assert retrieved == completed_entry
        
        # Non-existent UUID
        assert data.get_history_entry_by_uuid('fake-uuid') is None
    
    def test_remove_history_entry_by_uuid(self, temp_dir):
        """Test removing entry from history (with file cleanup)."""
        data = Data()
        data_path = os.path.join(temp_dir, 'data.json')
        data.path = data_path

        # Create temp file
        test_file = os.path.join(temp_dir, 'test.mp3')
        with open(test_file, 'w') as f:
            f.write('test')

        entry = Entry(url='http://test.com', filepath=test_file, status='completed')
        data.history.append(entry)

        assert os.path.exists(test_file)
        data.remove_history_entry_by_uuid(entry.uuid)

        assert len(data.history) == 0
        assert not os.path.exists(test_file)

    def test_remove_queue_entry_by_uuid(self, temp_dir):
        """Test removing entry from queue."""
        data = Data()
        data_path = os.path.join(temp_dir, 'data.json')
        data.path = data_path
        entry = Entry(url='http://test.com')
        data.add_to_queue(entry)

        assert len(data.queue) == 1
        data.remove_queue_entry_by_uuid(entry.uuid)
        assert len(data.queue) == 0

    def test_remove_entry_graceful_missing_file(self, temp_dir):
        """Test remove handles missing files gracefully (bug fix #9)."""
        data = Data()
        data_path = os.path.join(temp_dir, 'data.json')
        data.path = data_path
        entry = Entry(url='http://test.com', filepath='/nonexistent/file.mp3')
        data.history.append(entry)

        # Should not crash when file doesn't exist
        data.remove_history_entry_by_uuid(entry.uuid)
        assert len(data.history) == 0

    def test_remove_entry_graceful_none_filepath(self, temp_dir):
        """Test remove handles None filepath gracefully (bug fix #12)."""
        data = Data()
        data_path = os.path.join(temp_dir, 'data.json')
        data.path = data_path
        entry = Entry(url='http://test.com', filepath=None)
        data.queue.append(entry)

        # Should not crash with None filepath
        data.remove_queue_entry_by_uuid(entry.uuid)
        assert len(data.queue) == 0


class TestDataPersistence:
    """Tests for Data save/load functionality."""
    
    def test_save_and_load(self, temp_dir, sample_entry):
        """Test saving and loading Data."""
        data_path = os.path.join(temp_dir, 'data.json')
        
        data = Data()
        data.path = data_path
        data.add_to_queue(sample_entry)
        data.save(data_path)
        
        assert os.path.exists(data_path)
        
        # Load and verify
        loaded_data = Data.load(data_path)
        assert len(loaded_data.queue) == 1
        assert loaded_data.queue[0].url == sample_entry.url
    
    def test_load_nonexistent_returns_empty(self):
        """Test loading from nonexistent file returns empty Data."""
        data = Data.load('/nonexistent/path/data.json')
        assert len(data.queue) == 0
        assert len(data.history) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
