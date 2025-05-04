"""
Basic tests for the pywikicli package.
"""

import pytest
from pywikicli import __version__


def test_version():
    """Test that version is a string."""
    assert isinstance(__version__, str)


def test_config_module_imports():
    """Test that the config module can be imported."""
    from pywikicli import config

    assert hasattr(config, "load_config")
    assert hasattr(config, "save_config")


def test_api_module_imports():
    """Test that the api module can be imported."""
    from pywikicli import api

    assert hasattr(api, "WikiClient")
