#!/usr/bin/env python3

import requests
import json
import datetime
import sys
import subprocess
import argparse
import os
from typing import Optional

def load_config():
    """Load configuration from multiple sources with fallbacks"""
    result = {}
    
    # Try to load from config.py
    try:
        import config
        result['api_token'] = getattr(config, 'JOPLIN_API_TOKEN', None)
        result['base_url'] = getattr(config, 'JOPLIN_API_BASE_URL', 'http://localhost:41184')
        result['diary_folder_id'] = getattr(config, 'DIARY_FOLDER_ID', None)
        result['default_location'] = getattr(config, 'DEFAULT_LOCATION', 'Garrynacurry')
    except ImportError:
        pass
    
    # Override with environment variables if present
    result['api_token'] = os.getenv('JOPLIN_API_TOKEN', result.get('api_token'))
    result['base_url'] = os.getenv('JOPLIN_API_BASE_URL', result.get('base_url', 'http://localhost:41184'))
    result['diary_folder_id'] = os.getenv('JOPLIN_DIARY_FOLDER_ID', result.get('diary_folder_id'))
    result['default_location'] = os.getenv('JOPLIN_DEFAULT_LOCATION', result.get('default_location', 'Garrynacurry'))
    
    return result

class JoplinDiaryTool:
    def __init__(self, api_token: str, base_url: str = "http://localhost:41184", diary_folder_id: str = None, default_location: str = "Garrynacurry"):
        self.api_token = api_token
        self.base_url = base_url
        self.diary_folder_id = diary_folder_id or "3e68a3e8d7564e78b761dfe5162d637c"
        self.default_location = default_location
    
    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        params = {"token": self.api_token}
        
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, params=params, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # DELETE requests might not return JSON
        if method.upper() == "DELETE":
            return {"status": "deleted"}
        
        return response.json()
    
    def _is_valid_weather(self, weather_str: str) -> bool:
        """Validate weather string format"""
        if not weather_str or len(weather_str) > 100:
            return False
        invalid_indicators = ["error", "unknown", "not found", "404"]
        return not any(indicator in weather_str.lower() for indicator in invalid_indicators)
    
    def get_weather_info(self, location: str = "") -> str:
        """Get current weather information with fallbacks, optionally for specific location"""
        # Prepare location parameter for weather services
        location_param = f"/{location}" if location and location != "Garrynacurry" else ""
        
        # Primary weather source with location
        try:
            result = subprocess.run(['curl', '-s', f'wttr.in{location_param}?format=%C+%t'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and self._is_valid_weather(result.stdout.strip()):
                return result.stdout.strip()
        except Exception:
            pass
        
        # Fallback weather source with location
        try:
            result = subprocess.run(['curl', '-s', f'wttr.in{location_param}?format=3'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and self._is_valid_weather(result.stdout.strip()):
                weather_line = result.stdout.strip()
                # Extract just temperature if possible
                if ':' in weather_line:
                    weather_line = weather_line.split(':', 1)[1].strip()
                return weather_line
        except Exception:
            pass
        
        # Try without location if location-specific requests failed
        if location_param:
            try:
                result = subprocess.run(['curl', '-s', 'wttr.in/?format=%C+%t'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and self._is_valid_weather(result.stdout.strip()):
                    return result.stdout.strip()
            except Exception:
                pass
        
        # User input as last resort
        return input("Enter weather description (e.g., 'Mild, rainy. 11C'): ").strip()
    
    def get_location(self) -> tuple[str, str]:
        """Get current location using CoreLocation or configured default
        
        Returns:
            tuple: (location, source) where source is 'GPS', 'default', or 'override'
        """
        
        # Method 1: Try Swift CoreLocation helper (GPS accurate)
        location = self._try_corelocation()
        if location:
            return location, "GPS"
        
        # Method 2: Fall back to configured default location
        return self.default_location, "default"
    
    def _try_corelocation(self) -> Optional[str]:
        """Try to get location using Cocoa app bundle"""
        try:
            # Check if on macOS
            if sys.platform != 'darwin':
                return None
            
            # Check if app bundle exists
            script_dir = os.path.dirname(os.path.abspath(__file__))
            app_path = os.path.join(script_dir, 'JoplinLocationHelper.app')
            executable_path = os.path.join(app_path, 'Contents', 'MacOS', 'JoplinLocationHelper')
            
            if not os.path.exists(executable_path):
                return None
            
            # Run the app executable with timeout
            result = subprocess.run([executable_path], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout.strip():
                location = result.stdout.strip()
                if self._is_valid_location(location):
                    return location
                    
        except subprocess.TimeoutExpired:
            # Location request timed out
            pass
        except Exception:
            # Any other error (permissions denied, etc.)
            pass
        
        return None
    
    
    def _is_valid_location(self, location: str) -> bool:
        """Validate location string"""
        if not location or len(location) > 50:
            return False
        invalid_indicators = ["error", "unknown", "not found", "404", "null", "undefined"]
        return not any(indicator in location.lower() for indicator in invalid_indicators)
    
    def validate_entry_format(self, body: str, date: datetime.date) -> bool:
        """Validate the diary entry format"""
        lines = body.split('\n')
        
        if len(lines) < 6:
            return False
        
        # Check date format
        expected_date = date.strftime("%Y/%m/%d")
        if lines[0] != expected_date:
            return False
        
        # Check empty line after date
        if lines[1] != "":
            return False
        
        # Check weather line exists
        if not lines[2].strip():
            return False
        
        # Check day name
        expected_day = date.strftime("%A")
        if lines[3] != expected_day:
            return False
        
        # Check location
        if not lines[4].strip():
            return False
        
        return True
    
    def create_diary_entry(self, date: datetime.date, additional_content: str = "", dry_run: bool = False, location_override: str = None) -> dict:
        """Create a diary entry with automatic information and user content"""
        title = date.strftime("%Y/%m/%d")
        day_name = date.strftime("%A")
        formatted_date = date.strftime("%Y/%m/%d")
        
        # Get automatic information
        if location_override:
            location = location_override
            location_source = "override"
        else:
            location, location_source = self.get_location()
        
        weather = self.get_weather_info(location)
        
        # Build the diary entry body following 2025 format
        body_parts = [
            formatted_date,
            "",
            weather,
            day_name,
            location,
            "",
        ]
        
        # Add user content or template
        if additional_content.strip():
            body_parts.extend(additional_content.split('\n'))
        else:
            # Provide a template with some starter bullets
            body_parts.extend([
                "- ",
                "- ",
                "- "
            ])
        
        body = '\n'.join(body_parts)
        
        # Validate the entry format
        if not self.validate_entry_format(body, date):
            raise ValueError("Generated diary entry format is invalid")
        
        if dry_run:
            print("DRY RUN - Would create entry:")
            print(f"Title: {title}")
            print(f"Body:\n{body}")
            return {"id": "dry_run", "title": title, "body": body, "location_source": location_source}
        
        note_data = {
            "title": title,
            "body": body,
            "parent_id": self.diary_folder_id
        }
        
        result = self._make_request("POST", "/notes", note_data)
        result["location_source"] = location_source
        return result
    
    def check_existing_entry(self, date: datetime.date) -> Optional[dict]:
        """Check if diary entry already exists for the given date"""
        title = date.strftime("%Y/%m/%d")
        notes = self._make_request("GET", f"/folders/{self.diary_folder_id}/notes?fields=id,title")
        
        for note in notes.get("items", []):
            if note["title"] == title:
                return note
        return None

def run_integration_test(tool: JoplinDiaryTool):
    """Run integration test with real API calls but safe cleanup"""
    print("Running integration test...")
    
    # Test with a future date to avoid conflicts
    test_date = datetime.date(2025, 12, 31)
    test_content = "- Integration test entry\n- Testing automatic weather fetch\n- This will be deleted"
    
    try:
        # Check if test entry already exists
        existing = tool.check_existing_entry(test_date)
        if existing:
            print(f"Test entry already exists, deleting first...")
            tool._make_request("DELETE", f"/notes/{existing['id']}")
        
        # Create test entry
        print("Creating test entry...")
        result = tool.create_diary_entry(test_date, test_content)
        
        # Verify entry was created correctly
        print("Verifying entry format...")
        created_note = tool._make_request("GET", f"/notes/{result['id']}?fields=title,body")
        
        if not tool.validate_entry_format(created_note['body'], test_date):
            raise ValueError("Created entry format validation failed")
        
        print("✓ Entry format validation passed")
        
        # Test edge case dates
        edge_dates = [
            datetime.date(2024, 2, 29),  # Leap year
            datetime.date(2025, 1, 1),   # New year
            datetime.date(2025, 12, 31), # Year end
        ]
        
        for edge_date in edge_dates:
            try:
                temp_result = tool.create_diary_entry(edge_date, "- Edge case test", dry_run=True)
                if not tool.validate_entry_format(temp_result['body'], edge_date):
                    print(f"✗ Edge case validation failed for {edge_date}")
                else:
                    print(f"✓ Edge case validation passed for {edge_date}")
            except Exception as e:
                print(f"✗ Edge case failed for {edge_date}: {e}")
        
        # Clean up test entry
        print("Cleaning up test entry...")
        tool._make_request("DELETE", f"/notes/{result['id']}")
        
        # Verify cleanup
        try:
            tool._make_request("GET", f"/notes/{result['id']}")
            print("✗ Test entry was not properly deleted")
        except:
            print("✓ Test entry successfully deleted")
        
        print("✓ Integration test passed!")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True

def setup_config():
    """Interactive setup for configuration"""
    print("=== Joplin Diary Tool Setup ===")
    print()
    
    config_file_exists = os.path.exists('config.py')
    
    if not config_file_exists:
        print("Creating config.py from template...")
        with open('config.py.example', 'r') as example:
            content = example.read()
        
        with open('config.py', 'w') as config_file:
            config_file.write(content)
        
        print("✓ Created config.py")
    
    print("\nPlease edit config.py and update the following:")
    print("1. JOPLIN_API_TOKEN - Get from Joplin -> Tools -> Options -> Web Clipper")
    print("2. DIARY_FOLDER_ID - Your diary notebook ID (current default should work)")
    print("3. DEFAULT_LOCATION - Your preferred location fallback")
    print()
    print("Alternatively, you can set environment variables:")
    print("  export JOPLIN_API_TOKEN='your_token_here'")
    print("  export JOPLIN_DEFAULT_LOCATION='your_location'")
    print()
    print("Run the tool again after configuration is complete.")

def main():
    parser = argparse.ArgumentParser(description="Create diary entries in Joplin")
    parser.add_argument("date", nargs="?", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating it")
    parser.add_argument("--test", action="store_true", help="Run integration test")
    parser.add_argument("--setup", action="store_true", help="Help setup configuration")
    parser.add_argument("--location", type=str, help="Override location detection with specific location")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Check if setup is needed
    if args.setup or not config.get('api_token'):
        setup_config()
        return
    
    tool = JoplinDiaryTool(
        config['api_token'],
        config['base_url'],
        config['diary_folder_id'],
        config['default_location']
    )
    
    if args.test:
        run_integration_test(tool)
        return
    
    # Parse date argument
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = datetime.date.today()
    
    # Check if entry already exists
    existing = tool.check_existing_entry(target_date)
    if existing:
        print(f"Diary entry for {target_date} already exists (ID: {existing['id']})")
        overwrite = input("Overwrite? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    print(f"Creating diary entry for {target_date.strftime('%A, %B %d, %Y')}")
    print("Gathering automatic information...")
    
    # Show what location was detected
    if not args.dry_run:
        if args.location:
            print(f"Using location: {args.location} (manual override)")
        else:
            detected_location, location_source = tool.get_location()
            source_description = {
                "GPS": "GPS CoreLocation",
                "default": "configured default"
            }
            print(f"Using location: {detected_location} ({source_description[location_source]})")
        print("Fetching weather...")
    
    # Get user content (skip for dry-run)
    custom_content = ""
    if not args.dry_run:
        print("\nAdd your diary content below.")
        print("Start each activity with '- ' (dash space)")
        print("Use tabs for sub-bullets")
        print("Press Enter twice to finish:\n")
        
        content_lines = []
        empty_lines = 0
        
        while empty_lines < 2:
            try:
                line = input()
                if line == "":
                    empty_lines += 1
                else:
                    empty_lines = 0
                content_lines.append(line)
            except KeyboardInterrupt:
                print("\nCancelled.")
                sys.exit(0)
        
        # Remove the trailing empty lines
        custom_content = '\n'.join(content_lines[:-2]) if len(content_lines) > 2 else ""
    
    try:
        result = tool.create_diary_entry(target_date, custom_content, dry_run=args.dry_run, location_override=args.location)
        if not args.dry_run:
            print(f"\n✓ Diary entry created successfully!")
            print(f"Title: {target_date.strftime('%Y/%m/%d')}")
            print(f"Note ID: {result['id']}")
            
            # Show location source information
            location_source = result.get("location_source", "unknown")
            if args.location:
                print(f"Location: {args.location} (manual override)")
            else:
                final_location, _ = tool.get_location()
                source_description = {
                    "GPS": "GPS CoreLocation",
                    "default": "configured default"
                }
                print(f"Location: {final_location} ({source_description.get(location_source, location_source)})")
        else:
            # For dry-run, also show location source
            location_source = result.get("location_source", "unknown")
            if args.location:
                print(f"Location source: manual override")
            else:
                source_description = {
                    "GPS": "GPS CoreLocation", 
                    "default": "configured default"
                }
                print(f"Location source: {source_description.get(location_source, location_source)}")
    except Exception as e:
        print(f"Error creating diary entry: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()