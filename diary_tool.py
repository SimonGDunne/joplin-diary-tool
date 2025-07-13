#!/usr/bin/env python3

import requests
import json
import datetime
import sys
import subprocess
import argparse
from typing import Optional

class JoplinDiaryTool:
    def __init__(self, api_token: str, base_url: str = "http://localhost:41184"):
        self.api_token = api_token
        self.base_url = base_url
        self.diary_folder_id = "3e68a3e8d7564e78b761dfe5162d637c"
    
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
    
    def get_weather_info(self) -> str:
        """Get current weather information with fallbacks"""
        # Primary weather source
        try:
            result = subprocess.run(['curl', '-s', 'wttr.in/?format=%C+%t'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and self._is_valid_weather(result.stdout.strip()):
                return result.stdout.strip()
        except Exception:
            pass
        
        # Fallback weather source
        try:
            result = subprocess.run(['curl', '-s', 'wttr.in/?format=3'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and self._is_valid_weather(result.stdout.strip()):
                weather_line = result.stdout.strip()
                # Extract just temperature if possible
                if ':' in weather_line:
                    weather_line = weather_line.split(':', 1)[1].strip()
                return weather_line
        except Exception:
            pass
        
        # User input as last resort
        return input("Enter weather description (e.g., 'Mild, rainy. 11C'): ").strip()
    
    def get_location(self) -> str:
        """Get current location - defaults to Garrynacurry based on recent entries"""
        return "Garrynacurry"
    
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
    
    def create_diary_entry(self, date: datetime.date, additional_content: str = "", dry_run: bool = False) -> dict:
        """Create a diary entry with automatic information and user content"""
        title = date.strftime("%Y/%m/%d")
        day_name = date.strftime("%A")
        formatted_date = date.strftime("%Y/%m/%d")
        
        # Get automatic information
        weather = self.get_weather_info()
        location = self.get_location()
        
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
            return {"id": "dry_run", "title": title, "body": body}
        
        note_data = {
            "title": title,
            "body": body,
            "parent_id": self.diary_folder_id
        }
        
        return self._make_request("POST", "/notes", note_data)
    
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

def main():
    API_TOKEN = "f7e5f97b9c8a688ecbc3b07db67347acd3c39fa0941ee08ac5e4e7fa969a4b9811126ee17113cb8d702750a6038c4d23608fb25157df574dcc65930ab509b913"
    
    parser = argparse.ArgumentParser(description="Create diary entries in Joplin")
    parser.add_argument("date", nargs="?", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating it")
    parser.add_argument("--test", action="store_true", help="Run integration test")
    
    args = parser.parse_args()
    
    tool = JoplinDiaryTool(API_TOKEN)
    
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
    
    # Get weather info first so user can see it
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
        result = tool.create_diary_entry(target_date, custom_content, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"\n✓ Diary entry created successfully!")
            print(f"Title: {target_date.strftime('%Y/%m/%d')}")
            print(f"Note ID: {result['id']}")
            print(f"Location: {tool.get_location()}")
    except Exception as e:
        print(f"Error creating diary entry: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()