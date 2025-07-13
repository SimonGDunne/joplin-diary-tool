#!/bin/bash

echo "Building Joplin Location Helper app..."

# Build the Swift package
if ! swift build; then
    echo "❌ Failed to build Swift package"
    exit 1
fi

# Create app bundle structure
APP_NAME="JoplinLocationHelper.app"
APP_DIR="$APP_NAME/Contents"
MACOS_DIR="$APP_DIR/MacOS"
RESOURCES_DIR="$APP_DIR/Resources"

echo "Creating app bundle structure..."
rm -rf "$APP_NAME"
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy the executable
cp ".build/debug/JoplinLocationHelper" "$MACOS_DIR/"

# Create Info.plist in the right location
cp "Info.plist" "$APP_DIR/"

echo "✓ Created $APP_NAME"
echo ""
echo "The app is ready to use. When you first run it, macOS will ask for location permission."
echo "To test: open $APP_NAME"
echo ""
echo "The Python diary tool will automatically use this app for location detection."