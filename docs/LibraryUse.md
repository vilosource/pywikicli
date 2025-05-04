# Using PyWikiCLI Components in Your Scripts

This guide shows how to use PyWikiCLI's command components as a library in your own Python scripts.

## Key Components

### 1. Wiki Client
```python
from pywikicli.api import WikiClient

client = WikiClient(
    api_url="https://example.com/w/api.php",
    username="your_user",
    password="your_pass"
)
```

### 2. Crawl Strategies
```python
from pywikicli.commands.crawl_command import BreadthFirstStrategy, DepthFirstStrategy

# Use BFS (breadth-first search)
strategy = BreadthFirstStrategy()

# Or use DFS (depth-first search)
strategy = DepthFirstStrategy()
```

### 3. Page Processors
```python
from pywikicli.commands.crawl_command import FileOutputProcessor, ConsoleOutputProcessor

# For file output
file_processor = FileOutputProcessor("/path/to/output")

# For console output
console_processor = ConsoleOutputProcessor()
```

### 4. Crawler Service
```python
from pywikicli.commands.crawl_command import WikiCrawlerService

# Create crawler with client, processor, and strategy
crawler = WikiCrawlerService(
    wiki_client=client,
    processor=file_processor,
    strategy=strategy
)

# Run crawl
stats = crawler.crawl(
    start_page="Main_Page",
    max_depth=2,
    limit=50
)

print(f"Processed {stats['pages_processed']} pages")
```

## Complete Example
```python
from pywikicli.api import WikiClient
from pywikicli.commands.crawl_command import BreadthFirstStrategy, ConsoleOutputProcessor, WikiCrawlerService

# Initialize components
client = WikiClient(
    api_url="https://example.com/w/api.php",
    username="user",
    password="pass"
)

# Create crawler with console output and BFS
processor = ConsoleOutputProcessor()
strategy = BreadthFirstStrategy()
crawler = WikiCrawlerService(client, processor, strategy)

# Execute crawl
try:
    stats = crawler.crawl(
        start_page="Main_Page",
        max_depth=1,
        limit=10
    )
    print(f"Crawl completed: {stats['pages_processed']} pages processed")
except Exception as e:
    print(f"Error during crawl: {e}")
```

## Configuration
For production use, consider:
- Using environment variables for credentials
- Adding retry logic for API calls
- Implementing custom PageProcessors for specific output formats
- Using logging configuration for better debugging

## Error Handling
Always wrap crawl operations in try/except blocks to handle:
- Network errors
- API rate limiting
- Authentication failures
- Page not found errors

## Dependencies
Your script should have these dependencies:
```bash
pip install click pypandoc requests
```