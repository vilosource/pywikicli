"""
Implementation of the 'config' command for Wikibot CLI.
This command manages Wikibot configuration settings.
"""

import click
import os
import yaml
import logging
from wikibot.config import load_config, save_config, CONFIG_PATH

logger = logging.getLogger(__name__)

@click.command(name="config", help="Configure Wikibot settings")
@click.option('--api-url', help="API endpoint URL")
@click.option('--username', help="Wiki username")
@click.option('--password', help="Wiki password (or bot token)")
@click.option('--show', is_flag=True, help="Show current configuration")
def config_command(api_url, username, password, show):
    """
    Configure Wikibot settings or display current configuration.
    
    Args:
        api_url: MediaWiki API endpoint URL
        username: Username for authentication
        password: Password for authentication
        show: Flag to display current configuration
    """
    # Load current configuration
    current = load_config()
    
    # Show current configuration if requested
    if show:
        display = current.copy()
        if 'password' in display:
            display['password'] = '********'  # Mask password
        click.echo("Current configuration:")
        click.echo(yaml.safe_dump(display, default_flow_style=False))
        return
    
    # If no options specified, prompt for values interactively
    if not any([api_url, username, password]):
        click.echo("Enter configuration values (press Enter to keep current value):")
        api_url = click.prompt("Wiki API URL", default=current.get('api_url', ''))
        username = click.prompt("Username", default=current.get('username', ''))
        pwd = click.prompt("Password (hidden)", hide_input=True, default="", show_default=False)
        password = pwd or current.get('password', '')
    
    # Update configuration with new values
    new_cfg = current.copy()
    if api_url:
        new_cfg['api_url'] = api_url
    if username:
        new_cfg['username'] = username
    if password:
        new_cfg['password'] = password
    
    # Save updated configuration
    save_config(new_cfg)
    click.echo(f"Configuration saved to {CONFIG_PATH}")
    logger.debug(f"Configuration updated with API URL: {new_cfg.get('api_url')}, " 
                f"Username: {new_cfg.get('username')}")