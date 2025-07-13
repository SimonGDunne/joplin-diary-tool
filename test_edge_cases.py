#!/usr/bin/env python3

import datetime
from diary_tool import JoplinDiaryTool

def test_date_edge_cases():
    """Test date formatting edge cases without API calls"""
    print("Testing date edge cases...")
    
    # Mock tool for testing date formatting only
    tool = JoplinDiaryTool("fake_token")
    
    edge_cases = [
        (datetime.date(2024, 2, 29), "Leap year"),
        (datetime.date(2025, 1, 1), "New Year's Day"),
        (datetime.date(2025, 12, 31), "New Year's Eve"),
        (datetime.date(2025, 3, 30), "DST change"),
        (datetime.date(2025, 10, 26), "DST change back"),
    ]
    
    for test_date, description in edge_cases:
        try:
            # Test dry run to verify format without API calls
            result = tool.create_diary_entry(test_date, "- Test content", dry_run=True)
            
            # Verify the format manually
            lines = result['body'].split('\n')
            expected_date = test_date.strftime("%Y/%m/%d")
            expected_day = test_date.strftime("%A")
            
            assert lines[0] == expected_date, f"Date format wrong: {lines[0]} != {expected_date}"
            assert lines[3] == expected_day, f"Day format wrong: {lines[3]} != {expected_day}"
            
            print(f"✓ {description} ({test_date}): OK")
            
        except Exception as e:
            print(f"✗ {description} ({test_date}): {e}")

if __name__ == "__main__":
    test_date_edge_cases()