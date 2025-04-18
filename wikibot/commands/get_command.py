"""
Implementation of the 'get' command for Wikibot CLI.
This command fetches and displays wiki page content.
"""

import click
import logging
import os
import urllib.parse
import pypandoc
from wikibot.api import WikiClient

logger = logging.getLogger(__name__)

class WikiPageOutputHandler:
    """
    Handles output of wiki page content according to different format requirements.
    Following the Single Responsibility Principle by separating output handling logic.
    """
    
    def __init__(self, pagename, content):
        """Initialize with page name and content."""
        self.pagename = pagename
        self.content = content
        
    def get_default_filename(self, format_type="wiki"):
        """Generate a default filename based on the page name."""
        # Replace spaces with underscores for filename
        safe_name = self.pagename.replace(' ', '_').replace('/', '_')
        return f"{safe_name}.{format_type}"
        
    def convert_content(self, source_format="mediawiki", target_format="markdown"):
        """
        Convert content between formats using pandoc.
        
        Args:
            source_format: Input format (default: mediawiki)
            target_format: Output format (default: markdown)
            
        Returns:
            Converted content
        """
        try:
            return pypandoc.convert_text(
                self.content, 
                target_format,
                format=source_format
            )
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            # Fall back to original content
            return self.content
        
    def save_to_file(self, filepath, format_type="wiki"):
        """Save content to specified file path with proper format."""
        # Ensure directory exists
        if os.path.dirname(filepath) and not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
        # Apply format-specific transformations if needed
        content_to_save = self.content
        if format_type == "md" and self.content:
            # Convert from MediaWiki to Markdown using pandoc
            content_to_save = self.convert_content(
                source_format="mediawiki", 
                target_format="markdown"
            )
            
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_to_save)
        return filepath
        
    def output_to_console(self, format_type="wiki"):
        """
        Output content to console/stdout.
        
        Args:
            format_type: Format to display content in
        """
        if not self.content:
            return
            
        content_to_display = self.content
        if format_type == "md":
            # Convert from MediaWiki to Markdown for display
            content_to_display = self.convert_content(
                source_format="mediawiki", 
                target_format="markdown"
            )
            
        click.echo(content_to_display)


@click.command(name="get", help="Fetch and display a wiki page's content")
@click.argument('pagename')
@click.option('--save', is_flag=True, help="Save output to <PAGENAME>.wiki in current directory")
@click.option('--out', '-o', type=click.Path(), help="Save output to specific file path")
@click.option('--format', '-f', type=click.Choice(['wiki', 'md']), default='wiki', 
              help="Output format (wiki or markdown)")
@click.option('--get-url', is_flag=True, help="Display the full URL to the wiki page")
def get_command(pagename, save, out, format, get_url):
    """
    Fetch and display the content of a wiki page.
    
    Args:
        pagename: Name of the page to retrieve
        save: Flag to save output to default filename in current directory
        out: Optional specific file path to save the content to
        format: Output format (wiki or markdown)
        get_url: Flag to display the full URL to the wiki page
    """
    # Get configuration
    cfg = click.get_current_context().obj['config']
    
    # Ensure API URL is configured
    if 'api_url' not in cfg:
        click.echo("Error: API URL not configured. Run 'wikibot config' first.", err=True)
        return
    
    # Display the URL if requested
    if get_url:
        # Convert API URL to base wiki URL
        base_url = cfg['api_url'].replace('/api.php', '')
        # Create the full URL to the page (properly URL-encoded)
        page_url = f"{base_url}/index.php?title={urllib.parse.quote(pagename)}"
        click.echo(f"URL: {page_url}")
        # If only URL was requested, exit
        if not save and not out:
            return
    
    # Initialize client and get page - pass credentials for authentication if available
    client = WikiClient(
        cfg['api_url'],
        username=cfg.get('username'),
        password=cfg.get('password')
    )
    
    try:
        content = client.get_page(pagename)
        
        if content is None:
            click.echo(f"Page '{pagename}' not found.", err=True)
            return
            
        # Create output handler (Strategy pattern)
        output_handler = WikiPageOutputHandler(pagename, content)
        
        # Determine output destination
        if out:
            # User specified a custom output path
            filepath = output_handler.save_to_file(out, format)
            click.echo(f"Saved content of '{pagename}' to {filepath}")
        elif save:
            # Save to default filename in current directory
            default_file = output_handler.get_default_filename(format)
            filepath = output_handler.save_to_file(default_file, format)
            click.echo(f"Saved content of '{pagename}' to {filepath}")
        elif not get_url:
            # Output to console if not just URL requested
            output_handler.output_to_console(format)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)