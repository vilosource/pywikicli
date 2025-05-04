# Guide: Building Command-Line Clients for REST APIs (with Design Patterns)

This guide is for developers implementing command-line tools that interact with REST APIs, using Python as the primary language. It draws on best practices and patterns from the PyWikiCLI project and general software engineering principles.

---

## 1. Project Structure & Setup

Organize your project for clarity and maintainability:

```
mycli/
├── __init__.py
├── cli.py            # CLI entry point
├── config.py         # Configuration management
├── api.py            # REST API client(s)
├── commands/         # One module per CLI command
│   ├── __init__.py
│   ├── get_command.py
│   ├── put_command.py
│   └── ...
├── interfaces.py     # Abstract base classes (interfaces)
├── converters.py     # Optional: content/format converters
├── ...
```

- **cli.py**: Defines the main Click group and registers subcommands.
- **config.py**: Handles loading/saving config (YAML/JSON) in the user's home directory.
- **api.py**: Implements the REST API client logic.
- **commands/**: Each command (get, put, crawl, etc.) in its own file.
- **interfaces.py**: Abstract base classes for API, converters, etc.

---

## 2. Key Design Patterns

### 2.1. Single Responsibility Principle (SRP)
Each module/class should have one responsibility. For example, `config.py` only manages configuration, `api.py` only handles API calls, and each command module only implements CLI logic.

### 2.2. Factory Pattern
Use a factory to instantiate command handlers or API clients based on configuration or command-line arguments. This decouples creation logic from usage.

**Example:**
```python
# In api.py
class ApiClientFactory:
    @staticmethod
    def create(api_url, auth=None):
        return MyRestApiClient(api_url, auth)
```

### 2.3. Strategy Pattern
Encapsulate interchangeable algorithms or behaviors in separate classes. For example, different crawling strategies (BFS, DFS) or output processors (console, file).

**Example:**
```python
class OutputStrategy:
    def output(self, data):
        raise NotImplementedError

class ConsoleOutput(OutputStrategy):
    def output(self, data):
        print(data)

class FileOutput(OutputStrategy):
    def __init__(self, filename):
        self.filename = filename
    def output(self, data):
        with open(self.filename, 'w') as f:
            f.write(data)
```

### 2.4. Adapter Pattern
Wrap third-party libraries or APIs to provide a consistent interface to your application.

**Example:**
```python
class MyRestApiAdapter:
    def __init__(self, api_url):
        self.api_url = api_url
    def get_resource(self, resource_id):
        # Translate to actual HTTP request
        ...
```

### 2.5. Facade Pattern
Provide a unified interface to a set of interfaces in a subsystem. For example, a `WikiClient` that exposes `get_page`, `edit_page`, and `get_links` methods, hiding the complexity of authentication and HTTP requests.

**Example:**
```python
class WikiClient:
    def __init__(self, api_url, username, password):
        self.auth = AuthService(api_url, username, password)
        self.page = PageService(api_url, self.auth)
    def get_page(self, title):
        return self.page.get_page(title)
```

### 2.6. Registry Pattern
Maintain a registry of interchangeable components, such as content converters.

**Example:**
```python
class ConverterRegistry:
    _converters = []
    @classmethod
    def register(cls, converter):
        cls._converters.append(converter)
    @classmethod
    def get_converter(cls, source, target):
        for c in cls._converters:
            if c.can_convert(source, target):
                return c
```

---

## 3. CLI Implementation with Click

- Use the [Click](https://click.palletsprojects.com/) library for argument parsing and subcommands.
- Each command should be in its own module and registered in `cli.py`.
- Use docstrings for help text and examples (Click preserves newlines in docstrings).

**Example:**
```python
@click.command("get")
@click.argument("resource_id")
def get_command(resource_id):
    """
    Fetch and display a resource.

    Examples:
      mycli get 123
    """
    ...
```

---

## 4. Configuration Management

- Store config in a YAML or JSON file under `~/.mycli/`.
- Use secure permissions (e.g., `chmod 600`).
- Prompt for missing config on first run.

**Example:**
```python
import os, yaml
CONFIG_PATH = os.path.expanduser("~/.mycli/config.yaml")
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}
def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(cfg, f)
    os.chmod(CONFIG_PATH, 0o600)
```

---

## 5. REST API Client Implementation

- Use the `requests` library for HTTP calls.
- Separate authentication, resource access, and error handling into different classes or methods.
- Use logging for debugging and error reporting.

**Example:**
```python
import requests
class MyRestApiClient:
    def __init__(self, api_url, auth=None):
        self.api_url = api_url
        self.session = requests.Session()
        if auth:
            self.session.headers.update(auth.get_headers())
    def get_resource(self, resource_id):
        url = f"{self.api_url}/resource/{resource_id}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()
```

---

## 6. Error Handling & Logging

- Use Python's `logging` module for debug/info/error output.
- Print user-friendly error messages and exit with nonzero status on failure.
- Catch and handle exceptions at the command level.

**Example:**
```python
import logging
logger = logging.getLogger(__name__)
try:
    ...
except Exception as e:
    logger.error(f"Error: {e}")
    click.echo(f"An error occurred: {e}", err=True)
    sys.exit(1)
```

---

## 7. Testing

- Write unit tests for each module (use `pytest`).
- Mock HTTP requests for API client tests.
- Test CLI commands using Click's `CliRunner`.

---

## 8. Documentation & Examples

- Write clear docstrings for all modules, classes, and functions.
- Provide usage examples in command docstrings and the README.
- Document your design decisions and pattern usage.

---

## 9. Extensibility & Best Practices

- Follow SOLID principles for maintainability.
- Use design patterns to decouple logic and enable easy extension.
- Keep CLI, API, and business logic separate.
- Use environment variables for sensitive data if needed.
- Validate and sanitize all user input.

---

## 10. Example: Adding a New Command

Suppose you want to add a `delete` command:

1. Create `commands/delete_command.py`:
```python
import click
from mycli.api import MyRestApiClient
from mycli.config import load_config

@click.command("delete")
@click.argument("resource_id")
def delete_command(resource_id):
    """
    Delete a resource by ID.
    """
    cfg = load_config()
    client = MyRestApiClient(cfg['api_url'])
    try:
        client.delete_resource(resource_id)
        click.echo(f"Resource {resource_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
```
2. Register it in `cli.py`:
```python
from mycli.commands.delete_command import delete_command
cli.add_command(delete_command)
```

---

## 11. Further Reading
- [Click Documentation](https://click.palletsprojects.com/)
- [requests Documentation](https://docs.python-requests.org/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Design Patterns in Python](https://refactoring.guru/design-patterns/python)

---

By following this guide, you will be able to implement robust, maintainable, and extensible CLI tools for any REST API, using proven design patterns and best practices.
