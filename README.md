# PyWikiCLI

A command-line interface tool for interacting with MediaWiki-powered wikis.

## Features

- `get`: Retrieve and display wiki page content
- `put`: Edit or create wiki pages
- `crawl`: Crawl wiki pages starting from a specific page
- `config`: Configure API settings and credentials

## Installation

```bash
# Install from PyPI
pip install pywikicli

# Or install with Poetry
poetry install

# Activate the Poetry environment (if using Poetry)
poetry shell
```

## Usage

```bash
# Configure your wiki connection
wikicli config

# Get a page
wikicli get "Main Page"

# Get a page and save as Markdown
wikicli get "Main Page" -o md

# Put content to a page
wikicli put "My Page" --content "This is my wiki page content"

# Edit a page from a Markdown file
wikicli put my_page.md

# Crawl pages starting from a specific page
wikicli crawl "Starting Page" --depth 2
```

## Development

This project follows SOLID principles and uses a modular architecture for maintainability and extensibility.