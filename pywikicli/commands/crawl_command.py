"""
Implementation of the 'crawl' command for PyWikiCLI.
This command crawls wiki pages starting from a specific page.
"""

import click
import os
import logging
from collections import deque
from typing import List, Set, Tuple, Dict, Optional, Callable

from pywikicli.api import WikiClient
from pywikicli.interfaces import WikiApiInterface

logger = logging.getLogger(__name__)


class CrawlStrategy:
    """
    Defines the interface for wiki crawling strategies.
    Strategy pattern for different traversal algorithms.
    """
    
    @staticmethod
    def get_next(queue):
        """
        Get the next page to process from the queue.
        
        Args:
            queue: Queue of pages to process
            
        Returns:
            Tuple containing page and depth
        """
        raise NotImplementedError("Strategy must implement get_next")
    
    @staticmethod
    def add_page(queue, page, depth):
        """
        Add a page to the queue.
        
        Args:
            queue: Queue of pages to process
            page: Page to add
            depth: Depth of the page
        """
        raise NotImplementedError("Strategy must implement add_page")


class BreadthFirstStrategy(CrawlStrategy):
    """
    Breadth-first traversal strategy.
    Process all pages at one depth before moving to the next depth.
    """
    
    @staticmethod
    def get_next(queue):
        """
        Get the next page to process from the queue (FIFO).
        
        Args:
            queue: Queue of pages to process
            
        Returns:
            Tuple containing page and depth
        """
        return queue.popleft()
    
    @staticmethod
    def add_page(queue, page, depth):
        """
        Add a page to the end of the queue.
        
        Args:
            queue: Queue of pages to process
            page: Page to add
            depth: Depth of the page
        """
        queue.append((page, depth))


class DepthFirstStrategy(CrawlStrategy):
    """
    Depth-first traversal strategy.
    Follow links as deep as possible before backtracking.
    """
    
    @staticmethod
    def get_next(queue):
        """
        Get the next page to process from the queue (LIFO).
        
        Args:
            queue: Queue of pages to process
            
        Returns:
            Tuple containing page and depth
        """
        return queue.pop()
    
    @staticmethod
    def add_page(queue, page, depth):
        """
        Add a page to the end of the queue.
        
        Args:
            queue: Queue of pages to process
            page: Page to add
            depth: Depth of the page
        """
        queue.append((page, depth))


class PageProcessor:
    """
    Interface for processing a crawled page.
    Follows Single Responsibility Principle for page handling.
    """
    
    def process(self, page_title: str, content: str) -> None:
        """
        Process a page.
        
        Args:
            page_title: Title of the page
            content: Content of the page
        """
        raise NotImplementedError("Processor must implement process")


class FileOutputProcessor(PageProcessor):
    """
    Processor that saves pages to files.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize the processor.
        
        Args:
            output_dir: Directory to save files to
        """
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def process(self, page_title: str, content: str) -> None:
        """
        Save a page to a file.
        
        Args:
            page_title: Title of the page
            content: Content of the page
        """
        safe_name = page_title.replace(' ', '_').replace('/', '_') + '.txt'
        path = os.path.join(self.output_dir, safe_name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved '{page_title}' to {safe_name}")


class ConsoleOutputProcessor(PageProcessor):
    """
    Processor that outputs pages to the console.
    """
    
    def process(self, page_title: str, content: str) -> None:
        """
        Output a page to the console.
        
        Args:
            page_title: Title of the page
            content: Content of the page
        """
        click.echo(f"\n=== Page: {page_title} ===")
        # Truncate long content for console display
        click.echo(content[:500] + "..." if len(content) > 500 else content)


class WikiCrawlerService:
    """
    Service for crawling wiki pages.
    Encapsulates the crawling logic, following Single Responsibility Principle.
    """
    
    def __init__(self, wiki_client: WikiApiInterface, processor: PageProcessor, strategy: CrawlStrategy):
        """
        Initialize the crawler service.
        
        Args:
            wiki_client: Client for interacting with the wiki
            processor: Processor for handling crawled pages
            strategy: Strategy for traversing pages
        """
        self.wiki_client = wiki_client
        self.processor = processor
        self.strategy = strategy
        self.visited = set()
        self.pages_processed = 0
    
    def crawl(self, start_page: str, max_depth: int, limit: int) -> Dict[str, int]:
        """
        Crawl the wiki starting from a page.
        
        Args:
            start_page: Page to start crawling from
            max_depth: Maximum link depth to crawl
            limit: Maximum number of pages to process
            
        Returns:
            Statistics about the crawl
        """
        self.visited = set([start_page])
        queue = deque([(start_page, 0)])  # (page_title, depth)
        self.pages_processed = 0
        
        while queue and self.pages_processed < limit:
            # Get next page based on strategy
            page, cur_depth = self.strategy.get_next(queue)
            
            # Get page content
            content = self.wiki_client.get_page(page)
            if content is None:
                logger.warning(f"Page '{page}' does not exist, skipping")
                continue
                
            self.pages_processed += 1
            
            # Process the page
            self.processor.process(page, content)
            
            # Process links if we haven't reached max depth
            if cur_depth < max_depth:
                try:
                    links = self.wiki_client.get_links(page)
                    # Add new links to queue
                    for link in links:
                        if link not in self.visited:
                            self.visited.add(link)
                            self.strategy.add_page(queue, link, cur_depth+1)
                except Exception as e:
                    logger.error(f"Error getting links from '{page}': {e}")
        
        # Return statistics
        return {
            "pages_processed": self.pages_processed,
            "pages_discovered": len(self.visited)
        }


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
        click.echo("Error: API URL not configured. Run 'pywikicli config' first.", err=True)
        return
    
    # Initialize client with credentials if available
    client = WikiClient(
        cfg['api_url'],
        username=cfg.get('username'),
        password=cfg.get('password')
    )
    
    # Create appropriate processor
    if output_dir:
        processor = FileOutputProcessor(output_dir)
        click.echo(f"Saving pages to directory: {output_dir}")
    else:
        processor = ConsoleOutputProcessor()
    
    # Create appropriate strategy
    if strategy == 'bfs':
        crawl_strategy = BreadthFirstStrategy()
    else:
        crawl_strategy = DepthFirstStrategy()
    
    # Create and run crawler
    crawler = WikiCrawlerService(client, processor, crawl_strategy)
    
    click.echo(f"Starting crawl from '{startpage}' with {strategy} strategy, max depth {depth}, limit {limit} pages")
    
    try:
        stats = crawler.crawl(startpage, depth, limit)
        
        if stats["pages_processed"] >= limit:
            click.echo(f"\nCrawl stopped after reaching limit of {limit} pages")
        else:
            click.echo(f"\nCrawl complete. No more pages to process within depth {depth}")
            
        click.echo(f"Total pages processed: {stats['pages_processed']}")
        click.echo(f"Total pages discovered: {stats['pages_discovered']}")
        
    except Exception as e:
        click.echo(f"Error during crawl: {e}", err=True)
        logger.debug(f"Detailed error: {str(e)}", exc_info=True)