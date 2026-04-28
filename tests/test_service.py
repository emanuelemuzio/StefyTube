"""Unit tests for src/service.py - Service class methods."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from src.service import Service
from src.data import Entry, Data, Merge


class TestServiceDownloadEntry:
    """Tests for Service.download_entry method."""
    
    def test_download_entry_mp3_ffmpeg_path(self, mock_config):
        """Test download_entry sets correct FFmpeg path (bug fix #1)."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com', format='mp3')
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {
                'id': 'test',
                'title': 'Test',
                'webpage_url': 'http://test.com',
                '_filename': '/tmp/test.mp3'
            }
            
            service.download_entry(entry)
            
            # Verify FFmpeg location uses dirname, not full path
            call_args = mock_ydl.call_args
            ydl_opts = call_args[0][0]
            ffmpeg_location = ydl_opts['ffmpeg_location']
            
            # Should be directory, not exe file
            assert not ffmpeg_location.endswith('.exe')
            assert ffmpeg_location == os.path.dirname(mock_config.FFMPEG_PATH)
    
    def test_download_entry_mp3_postprocessor(self, mock_config):
        """Test MP3 postprocessor has keep_video option (bug fix #2)."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com', format='mp3')
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {
                'id': 'test',
                '_filename': '/tmp/test.mp3'
            }
            
            service.download_entry(entry)
            
            call_args = mock_ydl.call_args
            ydl_opts = call_args[0][0]
            postprocessors = ydl_opts['postprocessors']
            
            # Check FFmpegExtractAudio config
            pp = postprocessors[0]
            assert pp['key'] == 'FFmpegExtractAudio'
            assert pp['keep_video'] == False  # Bug fix
            assert pp['preferredcodec'] == 'mp3'
    
    def test_download_entry_filepath_extraction(self, mock_config):
        """Test correct filepath extraction after download (bug fix #4)."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com', format='mp3')
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            
            # Mock yt-dlp response with _filename
            mock_instance.extract_info.return_value = {
                'id': 'vid123',
                'title': 'Test Video',
                'webpage_url': 'http://test.com/vid123',
                '_filename': '/tmp/test_video.mp3',
                'ext': 'mp3'
            }
            
            # Create the actual file
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = os.path.join(tmpdir, 'test_video.mp3')
                with open(test_file, 'w') as f:
                    f.write('test')
                
                # Mock extract_info to return correct filename
                mock_instance.extract_info.return_value['_filename'] = test_file
                
                completed_entries = service.download_entry(entry)
                
                # Should have one completed entry
                assert len(completed_entries) == 1
                completed = completed_entries[0]
                
                # Filepath should be the actual output file
                assert completed.filepath == test_file
                assert completed.status == 'completed'
    
    def test_download_entry_mp3_file_verification(self, mock_config):
        """Test MP3 file verification after conversion (bug fix #5)."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com', format='mp3')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base_file = os.path.join(tmpdir, 'video')
            mp3_file = base_file + '.mp3'
            
            # Create the MP3 file
            with open(mp3_file, 'w') as f:
                f.write('mp3')
            
            with patch('yt_dlp.YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__.return_value = mock_instance
                mock_instance.extract_info.return_value = {
                    'id': 'test',
                    'title': 'Test',
                    'webpage_url': 'http://test.com',
                    '_filename': base_file
                }
                
                with patch('os.path.exists') as mock_exists:
                    mock_exists.return_value = True
                    
                    completed = service.download_entry(entry)
                    
                    # Should verify MP3 exists
                    assert len(completed) == 1
                    assert completed[0].format == 'mp3'
    
    def test_download_entry_playlist(self, mock_config):
        """Test downloading playlist creates multiple entries."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com/playlist', format='mp3', noplaylist=False)
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            
            # Mock playlist response
            mock_instance.extract_info.return_value = {
                'entries': [
                    {
                        'id': 'vid1',
                        'title': 'Video 1',
                        'webpage_url': 'http://youtube.com/watch?v=vid1',
                        '_filename': '/tmp/video1.mp3'
                    },
                    {
                        'id': 'vid2',
                        'title': 'Video 2',
                        'webpage_url': 'http://youtube.com/watch?v=vid2',
                        '_filename': '/tmp/video2.mp3'
                    }
                ]
            }
            
            completed = service.download_entry(entry)
            
            # Should have entries for each video
            assert len(completed) == 2
            assert completed[0].id == 'vid1'
            assert completed[1].id == 'vid2'
    
    def test_download_entry_exception_handling(self, mock_config):
        """Test download_entry handles exceptions gracefully."""
        service = Service(config=mock_config)
        entry = Entry(url='http://invalid.com', format='mp3')
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = Exception('Download failed')
            
            completed = service.download_entry(entry)
            
            # Should return entry with failed status
            assert len(completed) == 1
            assert completed[0].status == 'failed'


class TestServiceMerge:
    """Tests for Service.merge_uuid_list method."""
    
    def test_merge_file_validation(self, mock_config):
        """Test merge validates input files exist (bug fix #9)."""
        service = Service(config=mock_config)
        data = Data()
        data.path = mock_config.DATA_PATH

        from src.requests import MergeUuidList

        # Add entries with non-existent files
        entry1 = Entry(url='http://test1.com', filepath='/nonexistent/file1.mp3', status='completed')
        data.history.append(entry1)

        merge_request = MergeUuidList(uuids=[entry1.uuid], title='Test Merge')

        with pytest.raises(ValueError, match='Input file not found'):
            service.merge_uuid_list(data, merge_request)

    def test_merge_unique_output_naming(self, mock_config, temp_mp3_files):
        """Test merge creates unique output filename (bug fix #11)."""
        service = Service(config=mock_config)
        data = Data()
        data.path = mock_config.DATA_PATH

        from src.requests import MergeUuidList

        # Add entries
        entry1 = Entry(url='http://test1.com', filepath=temp_mp3_files[0], status='completed')
        entry2 = Entry(url='http://test2.com', filepath=temp_mp3_files[1], status='completed')
        data.history.extend([entry1, entry2])

        # Create existing output file
        output_file = os.path.join(mock_config.MERGE_DIR, 'test_merge.mp3')
        with open(output_file, 'w') as f:
            f.write('existing')

        merge_request = MergeUuidList(uuids=[entry1.uuid, entry2.uuid], title='test_merge')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            service.merge_uuid_list(data, merge_request)

            # Check that a unique name was created
            added_merge = data.merge[0]
            assert added_merge.filepath != output_file
            assert 'test_merge_1' in added_merge.filepath

    def test_merge_error_logging(self, mock_config, temp_mp3_files):
        """Test merge logs errors properly (bug fix #11)."""
        service = Service(config=mock_config)
        data = Data()
        data.path = mock_config.DATA_PATH

        from src.requests import MergeUuidList

        entry1 = Entry(url='http://test1.com', filepath=temp_mp3_files[0], status='completed')
        entry2 = Entry(url='http://test2.com', filepath=temp_mp3_files[1], status='completed')
        data.history.extend([entry1, entry2])

        merge_request = MergeUuidList(uuids=[entry1.uuid, entry2.uuid], title='test_merge')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr='FFmpeg error')

            with pytest.raises(Exception, match='FFmpeg merge failed'):
                service.merge_uuid_list(data, merge_request)

            # Error should be logged
            mock_config.logger.log.assert_called()


class TestServiceFFmpegPaths:
    """Tests for FFmpeg path configuration fixes."""
    
    def test_ffmpeg_location_is_directory(self, mock_config):
        """Regression test: FFmpeg location should be directory (bug fix #1)."""
        service = Service(config=mock_config)
        entry = Entry(url='http://test.com', format='mp4')
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = {
                'id': 'test',
                '_filename': '/tmp/test.mkv'
            }
            
            service.download_entry(entry)
            
            call_args = mock_ydl.call_args
            ydl_opts = call_args[0][0]
            ffmpeg_location = ydl_opts['ffmpeg_location']
            
            # Should use dirname
            assert ffmpeg_location == os.path.dirname(mock_config.FFMPEG_PATH)
            assert os.path.isdir(ffmpeg_location) or ffmpeg_location == os.path.dirname(mock_config.FFMPEG_PATH)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
