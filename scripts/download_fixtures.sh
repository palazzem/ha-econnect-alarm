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
HASS_TESTS_FOLDER=$DOWNLOAD_FOLDER/core-$VERSION/tests/

# Remove previous folder if exists
if [ -d "tests/hass" ]; then
    echo "Removing previous tests/hass/ folder"
    rm -rf tests/hass
fi

# Download HASS version
echo "Downloading Home Assistant $VERSION in $DOWNLOAD_FOLDER"
curl -L https://github.com/home-assistant/core/archive/refs/tags/$VERSION.tar.gz -o $DOWNLOAD_FOLDER/$VERSION.tar.gz

# Extract HASS fixtures and tests helpers, excluding all components and actual tests
echo "Extracting tests/ folder from $VERSION.tar.gz"
tar -C $DOWNLOAD_FOLDER --exclude='*/components/*' --exclude='*/pylint/*' -xf $DOWNLOAD_FOLDER/$VERSION.tar.gz core-$VERSION/tests
find $HASS_TESTS_FOLDER -type f -name "test_*.py" -delete

# Recursively find and update imports
find $HASS_TESTS_FOLDER -type f -exec sed -i 's/from tests\./from tests.hass./g' {} +
mv $HASS_TESTS_FOLDER/conftest.py $HASS_TESTS_FOLDER/fixtures.py

# Copy Home Assistant fixtures
mv $HASS_TESTS_FOLDER ./tests/hass
echo "Home Assistant $VERSION tests are now in tests/hass/"
