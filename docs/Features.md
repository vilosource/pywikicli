# wikibot — MediaWiki Command‑Line Client

A lightweight CLI tool for editing and crawling MediaWiki pages locally, then synchronizing changes back to a remote server.

---

## 1. Overview

**Purpose.**  
`wikibot` enables users to fetch, edit, and publish MediaWiki content from the command line. It supports multiple wiki "profiles," configurable via a guided setup, and follows best practices in code design.

**Key Features.**  
- Profile management (multiple wikis, tokens, credentials)  
- Fetch (`get`), publish (`put`), and batch‑export (`crawl`) commands  
- SOLID, pattern‑driven codebase with clear in‑code documentation  
- Click‑based CLI parsing for extensibility  

---

## 2. Architecture & Development Guidelines

- **Design Principles:**  
  - Follow **SOLID** principles in each module (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).  
  - Leverage common **design patterns** (Factory, Strategy, Adapter, Repository, etc.) and annotate each usage in comments.

- **CLI Framework:**  
  - Use the [Click](https://click.palletsprojects.com/) library for argument parsing and subcommands.  
  - Provide clear `--help` output for each command and option.

- **Configuration Storage:**  
  - Store per‑profile settings (API URL, username, token) in a YAML or JSON file under `~/.wikibot/`.  
  - Ensure file permissions are secure (e.g. `chmod 600`).

- **Logging & Errors:**  
  - Integrate a configurable logging system (e.g. Python's `logging` module).  
  - Provide user‑friendly error messages for network issues, authentication failures, and parse errors.  
  - Exit with nonzero status on failure.

- **Testing & CI:**  
  - Write unit tests for core modules; mock HTTP interactions.  
  - Include linters (flake8, mypy) and run them in CI.

---

## 3. Configuration Commands

### 3.1 Initialize / Edit Profiles

- **First Run:**  
  If no config exists, automatically launch the setup wizard.

- **View/Edit an Existing Profile**  
  ```bash
  wikibot config --edit <PROFILE_NAME>
  ```

## 4. Command Reference
Note: Surround multi‑word page titles in quotes.
Filenames may use either .wiki or .md extensions interchangeably for wiki markup or Markdown.

### 4.1 Fetch a Page
```bash
wikibot get "<Page Title>"
```
Behavior:

- Retrieves page content via the MediaWiki API.
- Saves to ./<Page_Title>.wiki (spaces → underscores).
- Overwrites only if --force is specified.

### 4.2 Publish a Page
```bash
wikibot put <filename.{wiki,md}>
```
Behavior:

- Reads local file.
- Converts filename back to wiki page title.
- Issues an API call to update that page.
- Optionally add a --summary flag for edit summaries.
- Supports --minor and --bot edit flags.

### 4.3 Crawl / Batch Export
```bash
wikibot crawl "<Page Title>" --output {wiki,md}
```
Behavior:

- Recursively fetches the specified page and all its linked pages.
- Writes each to the current directory, preserving namespace hierarchy in subfolders.
- --max-depth N to limit recursion depth.
- --filter to include/exclude by regex on titles.

## 5. Examples
```bash
# 1. Set up a new profile
wikibot config --add

# 2. Use a specific profile to fetch a page
wikibot --profile corporate get "Company_Policies"

# 3. Edit locally, then push changes with an edit summary
wikibot put Company_Policies.wiki --summary "Updated phone number"

# 4. Export all pages linked from "DevOps Home" to Markdown
wikibot crawl "DevOps Home" --output md --max-depth 2
```

## 6. Extensibility & Future Work
- Plugin System: Support custom transformers (e.g. HTML → Markdown).
- Dry‑Run Mode: Show API calls without executing them.
- Authentication Enhancements: OAuth flows, session caching.
- Bulk Operations: Batch‑put from a directory.

## 7. Submission Checklist
- [ ] Adheres to SOLID + documented design‑pattern usage
- [ ] Complete Click‑based CLI with thorough help text
- [ ] Secure, user‑friendly profile configuration
- [ ] Robust logging and error handling
- [ ] Unit tests and CI integration
