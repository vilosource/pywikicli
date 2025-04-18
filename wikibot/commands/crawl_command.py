"""
Implementation of the 'crawl' command for Wikibot CLI.
This command crawls wiki pages starting from a specific page.
"""

import click
import os
import logging
from collections import deque
from wikibot.api import WikiClient

logger = logging.getLogger(__name__)

@click.command(name="crawl", help="Crawl a wiki starting from a page")
@click.argument('startpage')
@click.option('--depth', '-d', default=1, type=int, help="Link-depth to crawl")
@click.option('--output-dir', '-o', type=click.Path(file_okay=False), help="Directory to save pages")
@click.option('--strategy', '-s', type=click.Choice(['bfs', 'dfs']), default='bfs', 
              help="Traversal strategy: breadth-first or depth-first")
@click.option('--limit', '-l', default=100, type=int, help="Maximum number of pages to crawl")
def crawl_command(startpage, depth, output_dir, strategy, limit):
    """
    Crawl a wiki starting from a specific page, traversing links.
    
    Args:
        startpage: Starting page for the crawl
        depth: Link depth to crawl (default: 1)
        output_dir: Directory to save page content to
        strategy: Traversal strategy (bfs or dfs)
        limit: Maximum number of pages to crawl
    """
    # Get configuration
    cfg = click.get_current_context().obj['config']
    
    # Ensure API URL is configured
    if 'api_url' not in cfg:
        click.echo("Error: API URL not configured. Run 'wikibot config' first.", err=True)
        return
    
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        click.echo(f"Saving pages to directory: {output_dir}")
    
    # Initialize client with credentials if available
    client = WikiClient(
        cfg['api_url'],
        username=cfg.get('username'),
        password=cfg.get('password')
    )
    
    # Track visited pages and queue
    visited = set([startpage])
    queue = deque([(startpage, 0)])  # (page_title, depth)
    pages_processed = 0
    
    click.echo(f"Starting crawl from '{startpage}' with {strategy} strategy, max depth {depth}, limit {limit} pages")
    
    try:
        while queue and pages_processed < limit:
            # Get next page based on strategy
            if strategy == 'bfs':
                page, cur_depth = queue.popleft()  # Breadth-first
            else:
                page, cur_depth = queue.pop()  # Depth-first
            
            # Get page content
            content = client.get_page(page)
            if content is None:
                logger.warning(f"Page '{page}' does not exist, skipping")
                continue
                
            pages_processed += 1
            
            # Save or display content
            if output_dir:
                safe_name = page.replace(' ', '_').replace('/', '_') + '.txt'
                path = os.path.join(output_dir, safe_name)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Saved '{page}' to {safe_name}")
            else:
                click.echo(f"\n=== Page: {page} ===")
                click.echo(content[:500] + "..." if len(content) > 500 else content)
            
            # Process links if we haven't reached max depth
            if cur_depth < depth:
                try:
                    links = client.get_links(page)
                    # Add new links to queue
                    for link in links:
                        if link not in visited:
                            visited.add(link)
                            queue.append((link, cur_depth+1))
                except Exception as e:
                    logger.error(f"Error getting links from '{page}': {e}")
        
        if pages_processed >= limit:
            click.echo(f"\nCrawl stopped after reaching limit of {limit} pages")
        else:
            click.echo(f"\nCrawl complete. No more pages to process within depth {depth}")
            
        click.echo(f"Total pages processed: {pages_processed}")
        click.echo(f"Total pages discovered: {len(visited)}")
        
    except Exception as e:
        click.echo(f"Error during crawl: {e}", err=True)
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)