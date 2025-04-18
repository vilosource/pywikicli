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
pywikicli config

# Get a page
pywikicli get "Main Page"

# Put content to a page
pywikicli put "My Page" --content "This is my wiki page content"

# Crawl pages starting from a specific page
pywikicli crawl "Starting Page" --depth 2
```

## Development

This project follows SOLID principles and uses a modular architecture for maintainability and extensibility.