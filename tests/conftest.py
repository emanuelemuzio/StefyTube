"""
Test configuration and fixtures for StefyTube.
Place this file as: tests/conftest.py
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock config with temporary paths."""
    config = Mock()
    config.DOWNLOAD_DIR = os.path.join(temp_dir, 'download')
    config.MERGE_DIR = os.path.join(temp_dir, 'merge')
    config.FFMPEG_PATH = os.path.join(temp_dir, 'ffmpeg.exe')
    config.DATA_PATH = os.path.join(temp_dir, 'data.json')
    config.BASE_DIR = temp_dir
    config.TEMPLATE_DIR = os.path.join(temp_dir, 'templates')
    config.STATIC_DIR = os.path.join(temp_dir, 'static')
    config.host = '127.0.0.1'
    config.port = 5000
    config.BASE_URL = 'http://127.0.0.1:5000'
    config.APP_NAME = 'StefyTube'
    config.LOG_PATH = os.path.join(temp_dir, 'test.log')
    config.logger = Mock()

    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.MERGE_DIR, exist_ok=True)

    return config


@pytest.fixture
def sample_entry():
    """Create a sample Entry."""
    from src.data import Entry
    return Entry(
        id='test_video_123',
        url='https://www.youtube.com/watch?v=test123',
        title='Test Video',
        format='mp3',
        status='queued'
    )


@pytest.fixture
def sample_entry_mp4():
    """Create a sample MP4 Entry."""
    from src.data import Entry
    return Entry(
        id='test_video_456',
        url='https://www.youtube.com/watch?v=test456',
        title='Test Video MP4',
        format='mp4',
        status='queued'
    )


@pytest.fixture
def data_object():
    """Create an empty Data object."""
    from src.data import Data
    return Data()


@pytest.fixture
def data_with_entries(sample_entry, sample_entry_mp4):
    """Create Data object with sample entries."""
    from src.data import Data
    data = Data()
    data.add_to_queue(sample_entry)
    data.add_to_queue(sample_entry_mp4)
    return data


@pytest.fixture
def temp_mp3_files(temp_dir):
    """Create temporary MP3 files for testing."""
    files = []
    for i in range(3):
        filepath = os.path.join(temp_dir, f'test_{i}.mp3')
        with open(filepath, 'wb') as f:
            f.write(b'ID3' + b'\x00' * 100)
        files.append(filepath)
    return files
