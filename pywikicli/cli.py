"""
CLI entry point for PyWikiCLI.
Defines the main command group and registers subcommands.
"""

import click
import logging
from pywikicli.config import load_config

@click.group(help="PyWikiCLI - interact with a MediaWiki via its API")
@click.option('--debug/--no-debug', default=False, help="Enable debug output")
@click.pass_context
def cli(ctx, debug):
    """Main entry point for PyWikiCLI."""
    # Set up logging
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    
    # Initialize context object for sharing data between commands
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()


# Import and register subcommands
from pywikicli.commands.get_command import get_command
from pywikicli.commands.put_command import put_command
from pywikicli.commands.crawl_command import crawl_command
from pywikicli.commands.config_command import config_command

cli.add_command(get_command)
cli.add_command(put_command)
cli.add_command(crawl_command)
cli.add_command(config_command)

if __name__ == '__main__':
    cli()