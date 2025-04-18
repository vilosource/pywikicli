#!/usr/bin/env bash
# bump_version.sh - Script to increment patch version and create a new release

# Ensure script fails on any error
set -e

# Change to project root directory
cd "$(dirname "$0")"

# Step 1: Get current version before bump
CURRENT_VERSION=$(poetry version -s)
echo "Current version: $CURRENT_VERSION"

# Step 2: Bump patch version using poetry
poetry version patch
NEW_VERSION=$(poetry version -s)
echo "New version: $NEW_VERSION"

# Step 3: Update version in __init__.py
# This is needed because poetry only updates pyproject.toml
sed -i "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" wikibot/__init__.py
echo "Updated __init__.py version to $NEW_VERSION"

# Step 4: Regenerate lock file
poetry lock
echo "Lock file updated"

# Step 5: Commit the changes
git add pyproject.toml poetry.lock wikibot/__init__.py
git commit -m "Bump version to $NEW_VERSION"
echo "Changes committed"

# Step 6: Create and push tag
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
git push origin main
git push origin "v$NEW_VERSION"
echo "Pushed tag v$NEW_VERSION"

echo "Version bump complete! GitHub Actions should now create a release and publish to PyPI."
echo ""
echo "IMPORTANT: To publish to PyPI, ensure you have set the PYPI_API_TOKEN secret in your GitHub repository."
echo "If you haven't set up the token yet, follow these steps:"
echo "1. Create an API token at https://pypi.org/manage/account/token/"
echo "2. Add the token as a secret named PYPI_API_TOKEN in your GitHub repository settings"
echo "   (Settings > Secrets and variables > Actions > New repository secret)"