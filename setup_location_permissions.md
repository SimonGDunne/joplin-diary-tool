# Setting Up Location Permissions for Joplin Diary Tool

The location helper app needs permission to access your location. Here's how to set it up:

## Step 1: Build the Location App
```bash
./build_location_app.sh
```

## Step 2: Grant Location Permission

### Method A: System Preferences
1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Location Services**
2. Look for "JoplinLocationHelper" in the list
3. Check the box to enable location access
4. If not listed, you may need to run the app first: `open JoplinLocationHelper.app`

### Method B: Manual Permission Request
1. Run: `open JoplinLocationHelper.app`
2. If a permission dialog appears, click "Allow"
3. If no dialog appears, check System Preferences as above

## Step 3: Test Location Detection
```bash
# Test the app directly
JoplinLocationHelper.app/Contents/MacOS/JoplinLocationHelper

# Test with the diary tool
python3 diary_tool.py --dry-run
```

## Troubleshooting

**App says "Location request timed out"**
- The app doesn't have location permission yet
- Follow the System Preferences steps above

**App says "Unable to determine location"**
- Location services might be disabled globally
- Check System Preferences → Security & Privacy → Location Services (main toggle)

**Still not working?**
- The diary tool will fall back to network-based detection
- You can manually override: `python3 diary_tool.py --location "Your Location"`
- The configured default location (Garrynacurry) will be used as fallback

## What the App Does
- Uses the same location services as Maps, Weather, etc.
- Much more accurate than IP-based location
- Shows your actual location instead of ISP city
- Respects your privacy - location stays on your Mac