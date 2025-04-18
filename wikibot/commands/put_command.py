"""
Implementation of the 'put' command for Wikibot CLI.
This command uploads/edits wiki page content.
"""

import click
import logging
import os
import re
import pypandoc
from pathlib import Path
from wikibot.api import WikiClient

logger = logging.getLogger(__name__)

# Abstract base class for the Strategy pattern
class ContentConverter:
    """
    Abstract class defining the interface for content conversion strategies.
    Following the Strategy pattern to encapsulate different conversion algorithms.
    """
    def convert(self, content):
        """Convert content from source format to MediaWiki format"""
        raise NotImplementedError("Subclasses must implement convert()")
    
    @classmethod
    def get_converter(cls, file_path):
        """
        Factory method to create the appropriate converter based on file extension.
        This is an example of the Factory Method pattern.
        """
        ext = Path(file_path).suffix.lower() if file_path else None
        
        if ext == '.md':
            return MarkdownConverter()
        # Return default (pass-through) converter for wiki files or when no file
        return DefaultConverter()


class DefaultConverter(ContentConverter):
    """
    Default converter that passes content through unchanged.
    Implementing the Strategy pattern with a concrete strategy.
    """
    def convert(self, content):
        return content


class MarkdownConverter(ContentConverter):
    """
    Converter that transforms Markdown content to MediaWiki format.
    Implementing the Strategy pattern with a concrete strategy.
    """
    def convert(self, content):
        try:
            # Use pandoc to convert from markdown to mediawiki
            return pypandoc.convert_text(
                content,
                'mediawiki',
                format='markdown'
            )
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            # Fall back to original content
            return content


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
        click.echo("Error: API URL not configured. Run 'wikibot config' first.", err=True)
        return
        
    # Check if credentials are configured
    if 'username' not in cfg or 'password' not in cfg:
        click.echo("Error: Username and password required for editing. Run 'wikibot config' first.", err=True)
        return
    
    # Content determination - Command pattern: encapsulating all parameters needed for a request
    if file_or_page and os.path.isfile(file_or_page):
        # Get content from file
        with open(file_or_page, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        # Apply appropriate conversion based on file type - Strategy pattern
        converter = ContentConverter.get_converter(file_or_page)
        new_text = converter.convert(file_content)
        
        # If pagename not explicitly provided, derive it from filename - Adapter pattern
        if not pagename:
            pagename = PageNameExtractor.from_filename(file_or_page)
            
    elif content:
        # Use content provided directly
        new_text = content
    else:
        click.echo("Error: Provide content via --content option or specify a file path.", err=True)
        return
    
    # Ensure we have a page name
    if not pagename:
        click.echo("Error: Page name must be provided either via --pagename or in the filename.", err=True)
        return
    
    # Initialize client and edit page
    client = WikiClient(cfg['api_url'], cfg.get('username'), cfg.get('password'))
    
    # Prepare edit options - this demonstrates the Builder pattern conceptually
    edit_options = {}
    if minor:
        edit_options['minor'] = True
    if bot:
        edit_options['bot'] = True
        
    try:
        # Delegate to API client - following Dependency Inversion Principle
        client.edit_page(pagename, new_text, summary=summary, **edit_options)
        click.echo(f"Successfully updated page '{pagename}'.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)