#!/bin/bash
# Build script for Render deployment
# This script builds the frontend and prepares the app for production

echo "=== Starting Production Build ==="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Run this from the frontend directory."
    exit 1
fi

# Install dependencies (Render does this automatically, but just in case)
echo "Installing dependencies..."
npm ci

# Build the React app
echo "Building React app..."
npm run build

# Verify build succeeded
if [ ! -d "build" ]; then
    echo "Error: Build directory not created"
    exit 1
fi

# Output build info
echo "=== Build Complete ==="
echo "Build directory: $(pwd)/build"
echo "Build size: $(du -sh build | cut -f1)"
echo "Files: $(find build -type f | wc -l)"
