"""
Implementation of the 'config' command for PyWikiCLI.
This command manages PyWikiCLI configuration settings.
"""

import click
import yaml
import logging
from pywikicli.config import load_config, save_config, CONFIG_PATH

logger = logging.getLogger(__name__)


@click.command("config")
@click.option(
    "--api-url", prompt="MediaWiki API URL", help="URL of the MediaWiki API endpoint"
)
@click.option("--username", prompt="Username", help="Your wiki username")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Your wiki password",
)
def config_command(api_url, username, password):
    """
    Configure connection settings for the wiki.

    Examples:
      wikibot config --api-url "https://example.com/w/api.php" --username "user" --password "pass"
      wikibot config
    """
    # Load current configuration
    current = load_config()

    # Show current configuration if requested
    if not any([api_url, username, password]):
        display = current.copy()
        if "password" in display:
            display["password"] = "********"  # Mask password
        click.echo("Current configuration:")
        click.echo(yaml.safe_dump(display, default_flow_style=False))
        return

    # If no options specified, prompt for values interactively
    if not any([api_url, username, password]):
        click.echo("Enter configuration values (press Enter to keep current value):")
        api_url = click.prompt("Wiki API URL", default=current.get("api_url", ""))
        username = click.prompt("Username", default=current.get("username", ""))
        pwd = click.prompt(
            "Password (hidden)", hide_input=True, default="", show_default=False
        )
        password = pwd or current.get("password", "")

    # Update configuration with new values
    new_cfg = current.copy()
    if api_url:
        new_cfg["api_url"] = api_url
    if username:
        new_cfg["username"] = username
    if password:
        new_cfg["password"] = password

    # Save updated configuration
    save_config(new_cfg)
    click.echo(f"Configuration saved to {CONFIG_PATH}")
    logger.debug(
        f"Configuration updated with API URL: {new_cfg.get('api_url')}, "
        f"Username: {new_cfg.get('username')}"
    )
