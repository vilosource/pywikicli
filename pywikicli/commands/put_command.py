"""
Implementation of the 'put' command for PyWikiCLI.
"""

import click
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

from pywikicli.api import WikiClient
from pywikicli.interfaces import WikiApiInterface
from pywikicli.converters import ContentConverterRegistry, infer_format_from_filename

logger = logging.getLogger(__name__)


class PageNameExtractor:
    """
    Extracts page names from filenames.
    Follows the Single Responsibility Principle by separating this logic.
    """
    @staticmethod
    def from_filename(filename):
        """Extract page name from filename, removing extension and replacing underscores with spaces"""
        if not filename:
            return None
            
        # Remove extension and directory path
        base_name = os.path.basename(filename)
        page_name = os.path.splitext(base_name)[0]
        
        # Replace underscores with spaces (MediaWiki convention)
        return page_name.replace('_', ' ')


class PutCommandService:
    """
    Service class for handling the 'put' command logic.
    Following the Single Responsibility Principle by separating CLI handling from business logic.
    """
    
    def __init__(self, wiki_client: WikiApiInterface):
        """
        Initialize the service with dependencies.
        
        Args:
            wiki_client: Client for interacting with wiki APIs
        """
        self.wiki_client = wiki_client
    
    def load_content_from_file(self, file_path: str) -> tuple[str, str]:
        """
        Load content from a file and determine its format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            tuple[str, str]: (content, format)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Infer format from file extension
        source_format = infer_format_from_filename(file_path)
        return content, source_format
    
    def convert_to_wiki_format(self, content: str, source_format: str) -> str:
        """
        Convert content to MediaWiki format if needed.
        
        Args:
            content: Content to convert
            source_format: Source format of the content
            
        Returns:
            str: Content in MediaWiki format
        """
        if source_format == "unknown" or source_format == "mediawiki":
            return content
        
        return ContentConverterRegistry.convert(content, source_format, "mediawiki")
    
    def update_wiki_page(self, page_title: str, content: str, summary: str, options: Dict[str, Any]) -> bool:
        """
        Update a wiki page with new content.
        
        Args:
            page_title: Title of the page to update
            content: New content for the page
            summary: Edit summary
            options: Additional options for the edit
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.wiki_client.edit_page(page_title, content, summary, **options)
    
    def get_page_url(self, page_title: str) -> Optional[str]:
        """
        Get URL to the wiki page if supported by the client.
        
        Args:
            page_title: Title of the page
            
        Returns:
            Optional[str]: URL to the page or None if not supported
        """
        if hasattr(self.wiki_client, 'get_page_url'):
            return self.wiki_client.get_page_url(page_title)
        return None


@click.command(name="put", help="Edit or create a wiki page with given content")
@click.argument('file_or_page', type=click.Path(exists=True), required=False)
@click.option('--pagename', '-p', help="Override the page name (default: derived from filename)")
@click.option('--content', '-c', help="New content as string")
@click.option('--summary', '-m', default="", help="Edit summary")
@click.option('--minor', is_flag=True, help="Mark as minor edit")
@click.option('--bot', is_flag=True, help="Mark as bot edit")
def put_command(file_or_page, pagename, content, summary, minor, bot):
    """
    Edit or create a wiki page with the given content.
    
    Args:
        file_or_page: File containing content to upload
        pagename: Override the page name (default: derived from filename)
        content: Content as a string (alternative to file)
        summary: Edit summary/comment
        minor: Flag to mark as minor edit
        bot: Flag to mark as bot edit
    """
    # Get configuration
    cfg = click.get_current_context().obj['config']
    
    # Ensure API URL is configured
    if 'api_url' not in cfg:
        click.echo("Error: API URL not configured. Run 'pywikicli config' first.", err=True)
        return
        
    # Check if credentials are configured
    if 'username' not in cfg or 'password' not in cfg:
        click.echo("Error: Username and password required for editing. Run 'pywikicli config' first.", err=True)
        return
    
    # Initialize client and service
    client = WikiClient(cfg['api_url'], cfg.get('username'), cfg.get('password'))
    service = PutCommandService(client)
    
    # Content determination
    wiki_content = None
    source_format = "mediawiki"  # Default format
    
    if file_or_page and os.path.isfile(file_or_page):
        # Get content from file
        file_content, source_format = service.load_content_from_file(file_or_page)
        wiki_content = service.convert_to_wiki_format(file_content, source_format)
        
        # If pagename not explicitly provided, derive it from filename
        if not pagename:
            pagename = PageNameExtractor.from_filename(file_or_page)
            
    elif content:
        # Use content provided directly
        wiki_content = content
    else:
        click.echo("Error: Provide content via --content option or specify a file path.", err=True)
        return
    
    # Ensure we have a page name
    if not pagename:
        click.echo("Error: Page name must be provided either via --pagename or in the filename.", err=True)
        return
    
    # Prepare edit options
    edit_options = {}
    if minor:
        edit_options['minor'] = True
    if bot:
        edit_options['bot'] = True
        
    try:
        # Update the wiki page
        success = service.update_wiki_page(pagename, wiki_content, summary, edit_options)
        if success:
            click.echo(f"Successfully updated page '{pagename}'.")
            
            # Show URL to the page if available
            page_url = service.get_page_url(pagename)
            if page_url:
                click.echo(f"Page URL: {page_url}")
        else:
            click.echo(f"Failed to update page '{pagename}'.", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)