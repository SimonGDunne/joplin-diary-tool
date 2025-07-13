# Joplin Diary Tool

A Python tool to automatically create diary entries in your local Joplin installation.

## Features

- **Automatic Information**: Fetches weather and date information automatically
- **Consistent Format**: Matches your existing diary entry format (2025 style)
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
- **Location**: Auto-detected via IP geolocation with fallback to "Garrynacurry"
- **Weather**: Fetched from wttr.in using detected location with multiple fallbacks
- **Day**: Day of week (Monday, Tuesday, etc.)

## Error Handling

- Location detection failure → falls back to "Garrynacurry"
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