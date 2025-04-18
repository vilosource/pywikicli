# Wikibot

A command-line interface tool for interacting with MediaWiki-powered wikis.

## Features

- `get`: Retrieve and display wiki page content
- `put`: Edit or create wiki pages
- `crawl`: Crawl wiki pages starting from a specific page
- `config`: Configure API settings and credentials

## Installation

```bash
# Install with Poetry
poetry install

# Activate the Poetry environment
poetry shell
```

## Usage

```bash
# Configure your wiki connection
wikibot config

# Get a page
wikibot get "Main Page"

# Put content to a page
wikibot put "My Page" --content "This is my wiki page content"

# Crawl pages starting from a specific page
wikibot crawl "Starting Page" --depth 2
```

## Development

This project follows SOLID principles and uses a modular architecture for maintainability and extensibility.