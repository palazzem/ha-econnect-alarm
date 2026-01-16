#!/bin/bash
#
# This script downloads a specified version of Home Assistant,
# extracts its test suite, processes the files, and moves them into a
# local 'tests/hass' directory for further use.
#
#   Usage: ./scripts/download_fixtures.sh <Home Assistant Version>
#   Example: ./scripts/download_fixtures.sh 2021.3.4
set -e

# Parameters
VERSION=$1

# Abort if no version is specified
if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/download_fixtures.sh <Home Assistant Version>"
    exit 1
fi

# Variables
DOWNLOAD_FOLDER=$(mktemp -d)
HASS_FOLDER="$DOWNLOAD_FOLDER/core-$VERSION"

# Remove previous folders if they exist
rm -rf tests/hass tests/script

# Download and extract Home Assistant
echo "Downloading Home Assistant $VERSION..."
curl -sL "https://github.com/home-assistant/core/archive/refs/tags/$VERSION.tar.gz" -o "$DOWNLOAD_FOLDER/$VERSION.tar.gz"

echo "Extracting fixtures..."
tar -C "$DOWNLOAD_FOLDER" -xf "$DOWNLOAD_FOLDER/$VERSION.tar.gz" \
    --exclude='*/components/*' \
    --exclude='*/pylint/*' \
    "core-$VERSION/tests" \
    "core-$VERSION/script/__init__.py" \
    "core-$VERSION/script/hassfest/__init__.py" \
    "core-$VERSION/script/hassfest/model.py"

# Process tests folder
find "$HASS_FOLDER/tests" -type f -name "test_*.py" -delete
find "$HASS_FOLDER" -type f -name "*.py" -exec perl -pi -e 's/from (tests|script)\./from tests.$1./g' {} +
mv "$HASS_FOLDER/tests/conftest.py" "$HASS_FOLDER/tests/fixtures.py"

# Move to final location
mv "$HASS_FOLDER/tests" ./tests/hass
mv "$HASS_FOLDER/script" ./tests/script

echo "Home Assistant $VERSION fixtures installed in tests/"
