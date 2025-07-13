# Joplin Diary Tool

A Python tool to automatically create diary entries in your local Joplin installation.

## Features

- **Automatic Information**: Fetches date, location, weather, and day automatically
- **GPS Location Detection**: Uses macOS CoreLocation for accurate positioning
- **Manual Location Override**: `--location` flag for travel or specific locations
- **Consistent Format**: Matches your existing diary entry format (2025 style)
- **Secure Configuration**: API tokens stored in config files, not code
- **Safe Testing**: Dry-run mode and comprehensive testing
- **Error Handling**: Graceful fallbacks for weather and network issues
- **Validation**: Built-in format validation

## Usage

### Create Today's Entry
```bash
python3 diary_tool.py
```

### Create Entry for Specific Date
```bash
python3 diary_tool.py 2025-07-15
```

### Preview Without Creating (Dry Run)
```bash
python3 diary_tool.py --dry-run 2025-07-15
```

### Run Tests
```bash
python3 diary_tool.py --test
python3 test_edge_cases.py
```

## Diary Format

The tool creates entries following your established format:

```
2025/07/15

Sunny +23°C
Tuesday
Garrynacurry

- Your diary content here
- Activities and thoughts
- Sub-bullets use tabs
```

## Automatic Information

- **Date**: YYYY/MM/DD format in title and body
- **Location**: Simple, reliable two-tier system
  - GPS CoreLocation (accurate, requires permission)
  - Configured default location (reliable fallback)
- **Weather**: Fetched from wttr.in using detected location with multiple fallbacks
- **Day**: Day of week (Monday, Tuesday, etc.)

## Configuration

### Setup
```bash
# First time setup
python3 diary_tool.py --setup

# Or set environment variables
export JOPLIN_API_TOKEN="your_token_here"
export JOPLIN_DEFAULT_LOCATION="your_location"
```

### Location Detection
The tool uses a simple, reliable two-tier system:
1. **macOS CoreLocation** - GPS-accurate location using built-in location services (requires one-time permission)
2. **Your configured default** - Reliable fallback for home/work location (Garrynacurry)

### Setup Location Services
```bash
# Build the location app (one time)
./build_location_app.sh

# Grant location permission (see setup_location_permissions.md)
open JoplinLocationHelper.app  # Triggers permission dialog

# Test location detection
python3 diary_tool.py --dry-run
```

### Manual Location Override
```bash
# Override automatic detection
python3 diary_tool.py --location "Nenagh"
python3 diary_tool.py --dry-run --location "Dublin"
```

## Location Behavior

**Automatic Detection:**
- ✅ **GPS available + permission granted** → Shows actual GPS location
- ✅ **GPS unavailable/denied** → Uses configured default (Garrynacurry)
- ✅ **Manual override** → `--location "Location"` always takes priority

**Benefits of Simplified System:**
- More predictable and reliable
- No confusing IP geolocation showing wrong cities
- Clear fallback behavior
- Manual control when needed

## Error Handling

- Location detection failure → uses configured default location
- Weather fetch failure → tries multiple services, then prompts for manual input
- Network issues → graceful degradation with fallbacks
- Format validation → prevents malformed entries
- Existing entries → prompts before overwriting

## Testing

The tool includes:
- Integration tests with real Joplin API calls
- Edge case testing (leap years, year boundaries)
- Format validation
- Safe cleanup of test data