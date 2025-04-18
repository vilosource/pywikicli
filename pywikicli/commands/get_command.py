"""
Implementation of the 'get' command for PyWikiCLI.
"""

import click
import logging
import os
import sys
from typing import Optional

from pywikicli.api import WikiClient, MediaWikiClient
from pywikicli.config import load_config
from pywikicli.interfaces import WikiApiInterface, UrlGenerator
from pywikicli.converters import ContentConverterRegistry, infer_format_from_filename

logger = logging.getLogger(__name__)


class GetCommandService:
    """
    Service class for handling the 'get' command logic.
    Following the Single Responsibility Principle by separating CLI handling from business logic.
    """
    
    def __init__(self, wiki_client: WikiApiInterface):
        """
        Initialize the service with dependencies.
        
        Args:
            wiki_client: Client for interacting with wiki APIs
        """
        self.wiki_client = wiki_client
    
    def fetch_page(self, page_title: str) -> Optional[str]:
        """
        Fetch content of a wiki page.
        
        Args:
            page_title: Title of the page to fetch
            
        Returns:
            Optional[str]: Page content or None if page doesn't exist
        """
        return self.wiki_client.get_page(page_title)
    
    def save_page_as_format(self, page_title: str, content: str, output_format: str) -> str:
        """
        Save page content to a file in the specified format.
        
        Args:
            page_title: Title of the page
            content: Content of the page
            output_format: Format to save as (e.g., "md", "html")
            
        Returns:
            str: Path to the saved file
        """
        # Map CLI format options to actual format names
        format_map = {
            "md": "markdown",
            "raw": "mediawiki",
            "html": "html",
        }
        target_format = format_map.get(output_format, "mediawiki")
        
        # Convert content if needed
        converted_content = ContentConverterRegistry.convert(content, "mediawiki", target_format)
        
        # Generate filename
        safe_name = page_title.replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}.{output_format}"
        
        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(converted_content)
            
        return filename
    
    def get_page_url(self, page_title: str) -> Optional[str]:
        """
        Get URL to the wiki page if supported by the client.
        
        Args:
            page_title: Title of the page
            
        Returns:
            Optional[str]: URL to the page or None if not supported
        """
        if isinstance(self.wiki_client, MediaWikiClient):
            return self.wiki_client.get_page_url(page_title)
        return None


@click.command("get")
@click.argument("page_title")
@click.option(
    "--output",
    "-o",
    "output_format",
    type=click.Choice(["md", "raw", "html"], case_sensitive=False),
    help="Output format. If specified, saves to <page_title>.<format>. Default is raw wiki text to stdout.",
)
@click.option(
    "--show-url",
    is_flag=True,
    help="Show the URL to the page"
)
@click.pass_context
def get_command(ctx, page_title, output_format, show_url):
    """
    Fetch and display the content of a MediaWiki page.
    
    Examples:
        wikicli get "Main Page"
        wikicli get "Main Page" -o md
        wikicli get "Main Page" --show-url
    """
    config = load_config()
    client = WikiClient(config["api_url"], config.get("username"), config.get("password"))
    service = GetCommandService(client)

    try:
        # Fetch page content
        content = service.fetch_page(page_title)
        if not content:
            click.echo(f"Page '{page_title}' not found or has no content.", err=True)
            sys.exit(1)

        # Show URL if requested
        if show_url:
            page_url = service.get_page_url(page_title)
            if page_url:
                click.echo(f"Page URL: {page_url}")

        # Handle output according to format
        if output_format:
            try:
                filename = service.save_page_as_format(page_title, content, output_format)
                click.echo(f"Saved page '{page_title}' as {output_format} to {filename}")
            except FileNotFoundError:
                # Could be raised if pandoc is missing
                click.echo("Error: pandoc executable not found. Please install pandoc.", err=True)
                click.echo("See https://pandoc.org/installing.html", err=True)
                sys.exit(1)
            except Exception as e:
                click.echo(f"Error saving/converting file: {e}", err=True)
                sys.exit(1)
        else:
            # Default: print raw wiki text to stdout
            click.echo(content)

    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)
        sys.exit(1)