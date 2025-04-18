"""
Basic tests for the wikibot package.
"""

import pytest
from wikibot import __version__

def test_version():
    """Test that version is a string."""
    assert isinstance(__version__, str)
    
def test_config_module_imports():
    """Test that the config module can be imported."""
    from wikibot import config
    assert hasattr(config, 'load_config')
    assert hasattr(config, 'save_config')
    
def test_api_module_imports():
    """Test that the api module can be imported."""
    from wikibot import api
    assert hasattr(api, 'WikiClient')