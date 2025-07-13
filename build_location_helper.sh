#!/bin/bash

# Build script for Swift location helper

echo "Building Swift location helper..."

# Compile the Swift script
if swiftc get_location.swift -o get_location; then
    echo "✓ Swift helper compiled successfully"
    
    # Make it executable
    chmod +x get_location
    echo "✓ Made executable"
    
    echo "Swift location helper is ready to use."
    echo ""
    echo "Note: The first time you run the diary tool, macOS will ask for"
    echo "location permission. Click 'Allow' to enable accurate location detection."
    
else
    echo "✗ Failed to compile Swift helper"
    exit 1
fi