"""
Content conversion implementations for PyWikiCLI.
Handles conversions between different formats (e.g., Markdown to MediaWiki).
"""

import logging
import pypandoc
from typing import Dict, Optional, List, Type
from pywikicli.interfaces import ContentConverter

logger = logging.getLogger(__name__)


class PandocConverter(ContentConverter):
    """
    Content converter that uses pandoc for format conversion.
    Supports multiple format conversions based on pandoc's capabilities.
    """
    
    # Map of supported format conversions
    SUPPORTED_CONVERSIONS = {
        ('markdown', 'mediawiki'): True,
        ('mediawiki', 'markdown'): True,
        ('html', 'mediawiki'): True,
        ('mediawiki', 'html'): True,
        ('markdown', 'html'): True,
        ('html', 'markdown'): True,
        # Add more supported formats as needed
    }
    
    def can_convert(self, source_format: str, target_format: str) -> bool:
        """
        Check if this converter supports the specified format conversion.
        
        Args:
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            bool: True if supported, False otherwise
        """
        return (source_format.lower(), target_format.lower()) in self.SUPPORTED_CONVERSIONS
    
    def convert(self, content: str, source_format: str, target_format: str) -> str:
        """
        Convert content from source format to target format using pandoc.
        
        Args:
            content: Content to convert
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            str: Converted content
        """
        if not self.can_convert(source_format, target_format):
            logger.warning(f"Unsupported conversion: {source_format} to {target_format}")
            return content
            
        try:
            return pypandoc.convert_text(
                content,
                target_format.lower(),
                format=source_format.lower()
            )
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            return content


class IdentityConverter(ContentConverter):
    """
    Identity converter that passes content through unchanged.
    Used as a fallback when no conversion is needed or possible.
    """
    
    def can_convert(self, source_format: str, target_format: str) -> bool:
        """
        Check if this converter supports the specified format conversion.
        Always returns True for identical formats.
        
        Args:
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            bool: True if source_format equals target_format, False otherwise
        """
        return source_format.lower() == target_format.lower()
    
    def convert(self, content: str, source_format: str, target_format: str) -> str:
        """
        Pass content through unchanged.
        
        Args:
            content: Content to convert
            source_format: Source content format (ignored)
            target_format: Target content format (ignored)
            
        Returns:
            str: Original content
        """
        return content


class ContentConverterRegistry:
    """
    Registry of content converters.
    Follows the Registry pattern for locating appropriate converters.
    """
    
    _converters: List[ContentConverter] = []
    
    @classmethod
    def register(cls, converter: ContentConverter) -> None:
        """
        Register a converter.
        
        Args:
            converter: Converter instance to register
        """
        cls._converters.append(converter)
    
    @classmethod
    def get_converter(cls, source_format: str, target_format: str) -> Optional[ContentConverter]:
        """
        Get a converter that can handle the specified format conversion.
        
        Args:
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            Optional[ContentConverter]: Appropriate converter or None if none found
        """
        # First check if formats are the same - use identity converter
        if source_format.lower() == target_format.lower():
            return IdentityConverter()
            
        # Find a converter that supports this conversion
        for converter in cls._converters:
            if converter.can_convert(source_format, target_format):
                return converter
                
        # No converter found
        return None
    
    @classmethod
    def convert(cls, content: str, source_format: str, target_format: str) -> str:
        """
        Convert content from source format to target format.
        
        Args:
            content: Content to convert
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            str: Converted content or original content if no converter found
        """
        converter = cls.get_converter(source_format, target_format)
        if converter:
            return converter.convert(content, source_format, target_format)
        else:
            logger.warning(f"No converter found for {source_format} to {target_format}")
            return content


# Register built-in converters
ContentConverterRegistry.register(PandocConverter())
ContentConverterRegistry.register(IdentityConverter())


def infer_format_from_filename(filename: str) -> str:
    """
    Infer content format from filename extension.
    
    Args:
        filename: Filename to inspect
        
    Returns:
        str: Inferred format (e.g., "markdown", "mediawiki") or "unknown"
    """
    if not filename:
        return "unknown"
        
    # Get file extension (lowercase, without leading dot)
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Map extensions to formats
    format_map = {
        'md': 'markdown',
        'markdown': 'markdown',
        'wiki': 'mediawiki',
        'mediawiki': 'mediawiki',
        'html': 'html',
        'htm': 'html',
        'txt': 'text',
    }
    
    return format_map.get(ext, "unknown")