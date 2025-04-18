# Wikibot CLI Implementation Guide

## Introduction

Welcome to the implementation guide for **Wikibot**, a Python CLI tool for interacting with MediaWiki-powered wikis. Wikibot will allow users to retrieve wiki page content, edit or create pages, crawl through multiple pages, and manage configuration for connecting to a MediaWiki API. It uses the MediaWiki Action API – a RESTful web service that allows users to perform wiki actions such as page retrieval, creation, editing, and searching. In practical terms, Wikibot will send HTTP requests (via the `requests` library) to a wiki’s API endpoint to login, fetch page content, or submit edits. This guide provides a detailed walkthrough of the project structure and coding practices to implement Wikibot, aimed at a junior developer. We will emphasize clean code architecture (following SOLID principles) and the use of design patterns to ensure the tool is maintainable and extensible.

By following this guide, you will set up the project with a clear folder structure, implement each CLI command using Python’s `Click` library for a friendly command-line interface, handle configuration securely with YAML, and adhere to best practices (documentation, logging, etc.). The end result will be a pip-installable CLI tool that can be easily distributed and used by others.

## Features Overview

Wikibot’s functionality is organized into several **subcommands**, each responsible for a specific feature. Here are the main commands and their purpose:

- **`wikibot get <pagename>`** – Retrieve and display the content of a wiki page. This command will fetch the wikitext (source) of the given page from the MediaWiki API and output it to the console or a file.
- **`wikibot put <pagename>`** – Upload or update the content of a wiki page. This allows editing a page by providing new content (either via command-line arguments or a file). The command will use the API to log in (if needed) and push the changes.
- **`wikibot crawl <startpage>`** – Crawl a wiki starting from the given page. This will recursively traverse linked pages (with a depth or page limit) and retrieve their content. It’s useful for archiving or analyzing a set of pages.
- **`wikibot config [options]`** – Configure the Wikibot settings such as the wiki API URL and user credentials. This command manages a YAML configuration file stored in the user’s home directory for persistence of settings.

Each subcommand is accessed as `wikibot <command> ...` from the CLI. We will use `Click` to define these commands and their options in a user-friendly way (with help messages, etc.). For example, running `wikibot` with no arguments will show a help message listing the subcommands. Running `wikibot get --help` will show usage information for the **get** command.

## Architecture and Design Principles

To ensure the project is **maintainable, extensible, and clean**, we will follow established software design principles (SOLID) and apply relevant design patterns.

### SOLID Principles

- **Single Responsibility Principle (SRP):** Each component of Wikibot will have a single responsibility. For instance, one module will strictly handle configuration management, another module will handle the MediaWiki API communication, and separate classes or functions will implement each CLI command’s logic.
- **Open/Closed Principle (OCP):** The design should be open for extension but closed for modification. We achieve this by designing extensible command handlers. Adding new commands should not require altering existing core logic.
- **Liskov Substitution Principle (LSP):** If we use base classes or interfaces (for example, a generic `Command` interface that specific command classes implement), each subclass will be usable interchangeably.
- **Interface Segregation Principle (ISP):** We avoid creating large, monolithic classes or interfaces. For example, our `WikiClient` provides focused methods (`get_page`, `edit_page`, etc.) rather than a single method with multiple behaviors.
- **Dependency Inversion Principle (DIP):** High-level modules (CLI commands) depend on abstractions (like `WikiClient`) rather than concrete HTTP details. This makes it easier to mock HTTP interactions or swap out the HTTP library if needed.

### Design Patterns

- **Factory Pattern:** We will use a factory to instantiate command handlers or components based on command names, decoupling creation logic from usage.
- **Strategy Pattern:** For the crawl feature, different crawling algorithms (e.g., breadth-first vs depth-first) can be encapsulated in separate strategy classes.
- **Adapter Pattern:** The `WikiClient` class acts as an adapter between our application and the MediaWiki HTTP API, translating method calls into HTTP requests and JSON parsing.

## Project Structure

```
wikibot/               
├── __init__.py        
├── cli.py             
├── config.py          
├── api.py             
├── commands/          
│   ├── __init__.py
│   ├── get_command.py
│   ├── put_command.py
│   ├── crawl_command.py
│   └── config_command.py
requirements.txt      
setup.py              
README.md             
Implementation.md     
```

- **`cli.py`**: Entry point defining the Click group and registering subcommands.
- **`config.py`**: Handles loading and saving the YAML configuration under `~/.wikibot/`.
- **`api.py`**: Implements `WikiClient` for MediaWiki API interactions using `requests`.
- **`commands/`**: Contains one module per CLI subcommand, each implementing its logic.

## Dependencies and Requirements

In `requirements.txt`:
```
click>=8.1.3
requests>=2.28.0
PyYAML>=6.0
```

## Implementation Details

### CLI Setup with Click

In `cli.py`:
```python
import click
import logging
from wikibot.config import load_config

@click.group(help="Wikibot CLI - interact with a MediaWiki via its API")
@click.option('--debug/--no-debug', default=False, help="Enable debug output")
@click.pass_context
def cli(ctx, debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    ctx.obj = {}
    ctx.obj['config'] = load_config()
```
Register subcommands:
```python
from wikibot.commands.get_command import get_command
# similarly import other commands
cli.add_command(get_command)
# etc.
```

### Configuration Management

In `config.py`:
```python
import os
import yaml

CONFIG_DIR = os.path.expanduser("~/.wikibot")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def save_config(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(data, f)
    os.chmod(CONFIG_PATH, 0o600)
```

### MediaWiki API Client

In `api.py`:
```python
import requests
import logging

logger = logging.getLogger(__name__)

class WikiClient:
    def __init__(self, api_url: str, username: str = None, password: str = None):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Wikibot/0.1"})
        if username and password:
            self.login()

    def login(self):
        # fetch login token, post credentials, handle errors
        pass

    def get_page(self, title: str) -> str:
        # call action=query&prop=revisions to fetch wikitext
        pass

    def edit_page(self, title: str, new_content: str, summary: str = ""):
        # ensure login, fetch CSRF token, post edit
        pass

    def get_links(self, title: str) -> list:
        # call action=query&prop=links to list linked pages
        pass
```

### `get` Command

In `commands/get_command.py`:
```python
import click
import logging
from wikibot.api import WikiClient
from wikibot.config import load_config

logger = logging.getLogger(__name__)

@click.command(name="get", help="Fetch and display a wiki page's content")
@click.argument('pagename')
@click.option('--out', '-o', type=click.Path(), help="Save output to file")
def get_command(pagename, out):
    cfg = load_config()
    client = WikiClient(cfg['api_url'])
    content = client.get_page(pagename)
    if content is None:
        click.echo(f"Page '{pagename}' not found.", err=True)
        return
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(content)
        click.echo(f"Saved content of '{pagename}' to {out}")
    else:
        click.echo(content)
```

### `put` Command

In `commands/put_command.py`:
```python
import click
import logging
from wikibot.api import WikiClient
from wikibot.config import load_config

logger = logging.getLogger(__name__)

@click.command(name="put", help="Edit or create a wiki page with given content")
@click.argument('pagename')
@click.option('--content', '-c', help="New content as string")
@click.option('--file', '-f', type=click.File('r'), help="File with new content")
@click.option('--summary', '-m', default="", help="Edit summary")
def put_command(pagename, content, file, summary):
    cfg = load_config()
    client = WikiClient(cfg['api_url'], cfg.get('username'), cfg.get('password'))
    if file:
        new_text = file.read()
    else:
        new_text = content
    if not new_text:
        click.echo("Provide content via --content or --file.", err=True)
        return
    try:
        client.edit_page(pagename, new_text, summary=summary)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return
    click.echo(f"Page '{pagename}' has been updated successfully.")
```

### `crawl` Command

In `commands/crawl_command.py`:
```python
import click
import os
from collections import deque
from wikibot.api import WikiClient
from wikibot.config import load_config

@click.command(name="crawl", help="Crawl a wiki starting from a page")
@click.argument('startpage')
@click.option('--depth', '-d', default=1, help="Link-depth to crawl")
@click.option('--output-dir', '-o', type=click.Path(file_okay=False), help="Directory to save pages")
@click.option('--strategy', '-s', type=click.Choice(['bfs','dfs']), default='bfs')
def crawl_command(startpage, depth, output_dir, strategy):
    cfg = load_config()
    client = WikiClient(cfg['api_url'])
    visited = set([startpage])
    queue = deque([(startpage, 0)])
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    while queue:
        page, cur_depth = queue.popleft() if strategy == 'bfs' else queue.pop()
        content = client.get_page(page)
        if content:
            if output_dir:
                safe_name = page.replace(' ', '_').replace('/', '_') + '.txt'
                path = os.path.join(output_dir, safe_name)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                click.echo(f"=== Page: {page} ===")
                click.echo(content)
        if cur_depth < depth:
            links = client.get_links(page)
            for link in links:
                if link not in visited:
                    visited.add(link)
                    queue.append((link, cur_depth+1))
    click.echo(f"Crawl complete. {len(visited)} pages processed.")
```

### `config` Command

In `commands/config_command.py`:
```python
import click
import os
import yaml
from wikibot.config import load_config, save_config, CONFIG_PATH

@click.command(name="config", help="Configure Wikibot settings")
@click.option('--api-url', help="API endpoint URL")
@click.option('--username', help="Wiki username")
@click.option('--password', help="Wiki password (or bot token)")
@click.option('--show', is_flag=True, help="Show current configuration")
def config_command(api_url, username, password, show):
    current = load_config()
    if show:
        display = current.copy()
        if 'password' in display:
            display['password'] = '********'
        click.echo(yaml.safe_dump(display, default_flow_style=False))
        return
    if not any([api_url, username, password]):
        api_url = click.prompt("Wiki API URL", default=current.get('api_url',''))
        username = click.prompt("Username", default=current.get('username',''))
        pwd = click.prompt("Password (hidden)", hide_input=True, default="", show_default=False)
        password = pwd or current.get('password','')
    new_cfg = current.copy()
    if api_url: new_cfg['api_url'] = api_url
    if username: new_cfg['username'] = username
    if password: new_cfg['password'] = password
    save_config(new_cfg)
    click.echo(f"Configuration saved to {CONFIG_PATH}")
```

## Logging

Configure logging in `cli.py` and use `logging.getLogger(__name__)` in each module. Use `--debug` to enable DEBUG level. Avoid logging sensitive data.

## Documentation and Comments

- Write clear module docstrings at top of each file.
- Use Google-style docstrings for classes and functions.
- Add inline comments to explain non-obvious logic, especially for crawl traversal and API token handling.

## Packaging

In `setup.py`:
```python
from setuptools import setup, find_packages

setup(
    name="wikibot",
    version="0.1.0",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "click>=8.1.3",
        "requests>=2.28.0",
        "PyYAML>=6.0"
    ],
    entry_points={
        'console_scripts': [
            'wikibot=wikibot.cli:cli',
        ],
    },
    author="Your Name",
    description="A CLI tool to interact with MediaWiki via its API"
)
```

Users can install with:
```bash
pip install .
```

---

By following this guide, you will implement a clean, SOLID‑based, well‑documented Python CLI tool for interacting with MediaWiki.