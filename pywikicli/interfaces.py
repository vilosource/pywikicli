"""
Interfaces for PyWikiCLI components.
Defines abstractions for different service responsibilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AuthenticationService(ABC):
    """Interface for wiki authentication services."""
    
    @abstractmethod
    def login(self) -> bool:
        """Authenticate with the wiki API.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        pass


class PageService(ABC):
    """Interface for wiki page operations."""
    
    @abstractmethod
    def get_page(self, title: str) -> Optional[str]:
        """Retrieve content of a wiki page.
        
        Args:
            title: Title of the wiki page
            
        Returns:
            Optional[str]: Page content or None if page doesn't exist
        """
        pass
    
    @abstractmethod
    def edit_page(self, title: str, content: str, summary: str = "", **options) -> bool:
        """Edit or create a wiki page.
        
        Args:
            title: Title of the wiki page
            content: New content for the page
            summary: Edit summary/comment
            **options: Additional edit options
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass


class LinkService(ABC):
    """Interface for wiki link operations."""
    
    @abstractmethod
    def get_links(self, title: str) -> List[str]:
        """Get all links from a wiki page.
        
        Args:
            title: Title of the wiki page
            
        Returns:
            List[str]: List of page titles linked from the page
        """
        pass


class WikiApiInterface(AuthenticationService, PageService, LinkService):
    """Composite interface for all wiki API operations."""
    pass


class ContentConverter(ABC):
    """Interface for content format conversion."""
    
    @abstractmethod
    def can_convert(self, source_format: str, target_format: str) -> bool:
        """Check if this converter supports the specified format conversion.
        
        Args:
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            bool: True if supported, False otherwise
        """
        pass
    
    @abstractmethod
    def convert(self, content: str, source_format: str, target_format: str) -> str:
        """Convert content from source format to target format.
        
        Args:
            content: Content to convert
            source_format: Source content format
            target_format: Target content format
            
        Returns:
            str: Converted content
        """
        pass


class UrlGenerator(ABC):
    """Interface for generating URLs to wiki resources."""
    
    @abstractmethod
    def get_page_url(self, page_title: str) -> str:
        """Generate URL to a wiki page.
        
        Args:
            page_title: Title of the wiki page
            
        Returns:
            str: URL to the wiki page
        """
        pass