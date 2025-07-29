"""
Validate Mappings Script
Validates mapping files and checks for common issues
"""

import csv
from pathlib import Path
import sys
from typing import Set, Dict, List, Tuple

def validate_mappings(mappings_dir: str = "./mappings") -> bool:
    """
    Validate all mapping files
    
    Args:
        mappings_dir: Directory containing mapping files
        
    Returns:
        True if all validations pass
    """
    mappings_path = Path(mappings_dir)
    
    if not mappings_path.exists():
        print(f"ERROR: Mappings directory not found: {mappings_path}")
        return False
    
    all_valid = True
    
    # Validate positions.csv
    print("\n=== Validating positions.csv ===")
    positions_valid, position_tags = validate_positions(mappings_path / "positions.csv")
    all_valid &= positions_valid
    
    # Validate locations.csv
    print("\n=== Validating locations.csv ===")
    locations_valid, location_tags = validate_locations(mappings_path / "locations.csv")
    all_valid &= locations_valid
    
    # Validate never_positions.csv
    print("\n=== Validating never_positions.csv ===")
    never_valid, never_positions = validate_never_positions(mappings_path / "never_positions.csv")
    all_valid &= never_valid
    
    # Cross-validation
    print("\n=== Cross-Validation ===")
    cross_valid = cross_validate(position_tags, location_tags, never_positions)
    all_valid &= cross_valid
    
    return all_valid


def validate_positions(file_path: Path) -> Tuple[bool, Set[str]]:
    """Validate positions.csv file"""
    if not file_path.exists():
        print(f"  ERROR: File not found: {file_path}")
        return False, set()
    
    valid = True
    tag_ids = set()
    positions = set()
    duplicates = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        if 'position' not in reader.fieldnames or 'id' not in reader.fieldnames:
            print(f"  ERROR: Missing required columns. Found: {reader.fieldnames}")
            return False, set()
        
        for i, row in enumerate(reader, start=2):
            position = row.get('position', '').strip()
            tag_id = row.get('id', '').strip()
            
            # Check for empty values
            if not position:
                print(f"  WARNING: Row {i} has empty position")
                valid = False
            if not tag_id:
                print(f"  WARNING: Row {i} has empty tag ID")
                valid = False
            
            # Check for duplicates
            if position in positions:
                duplicates.append(position)
            positions.add(position)
            
            # Validate tag ID format
            if tag_id and not tag_id.isdigit():
                print(f"  WARNING: Row {i} has non-numeric tag ID: {tag_id}")
            
            tag_ids.add(tag_id)
    
    print(f"  Total positions: {len(positions)}")
    print(f"  Unique tag IDs: {len(tag_ids)}")
    
    if duplicates:
        print(f"  WARNING: Duplicate positions found: {duplicates}")
        valid = False
    
    return valid, tag_ids


def validate_locations(file_path: Path) -> Tuple[bool, Set[str]]:
    """Validate locations.csv file"""
    if not file_path.exists():
        print(f"  ERROR: File not found: {file_path}")
        return False, set()
    
    valid = True
    tag_ids = set()
    locations = set()
    duplicates = []
    valid_timezones = {
        'America/New_York', 'America/Chicago', 'America/Denver', 
        'America/Los_Angeles', 'America/Phoenix', 'America/Anchorage',
        'Pacific/Honolulu'
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        required = {'location', 'id', 'timezone'}
        if not required.issubset(reader.fieldnames):
            print(f"  ERROR: Missing required columns. Found: {reader.fieldnames}")
            return False, set()
        
        for i, row in enumerate(reader, start=2):
            location = row.get('location', '').strip()
            tag_id = row.get('id', '').strip()
            timezone = row.get('timezone', '').strip()
            
            # Check for empty values
            if not location:
                print(f"  WARNING: Row {i} has empty location")
                valid = False
            if not tag_id:
                print(f"  WARNING: Row {i} has empty tag ID")
                valid = False
            if not timezone:
                print(f"  WARNING: Row {i} has empty timezone")
                valid = False
            
            # Check for duplicates
            if location in locations:
                duplicates.append(location)
            locations.add(location)
            
            # Validate tag ID format
            if tag_id and not tag_id.isdigit():
                print(f"  WARNING: Row {i} has non-numeric tag ID: {tag_id}")
            
            # Validate timezone
            if timezone and timezone not in valid_timezones:
                print(f"  INFO: Row {i} has uncommon timezone: {timezone}")
            
            tag_ids.add(tag_id)
    
    print(f"  Total locations: {len(locations)}")
    print(f"  Unique tag IDs: {len(tag_ids)}")
    
    if duplicates:
        print(f"  WARNING: Duplicate locations found: {duplicates}")
        valid = False
    
    return valid, tag_ids


def validate_never_positions(file_path: Path) -> Tuple[bool, Set[str]]:
    """Validate never_positions.csv file"""
    if not file_path.exists():
        print(f"  ERROR: File not found: {file_path}")
        return False, set()
    
    valid = True
    positions = set()
    duplicates = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        if 'never_position' not in reader.fieldnames:
            print(f"  ERROR: Missing required column. Found: {reader.fieldnames}")
            return False, set()
        
        for i, row in enumerate(reader, start=2):
            position = row.get('never_position', '').strip()
            
            # Check for empty values
            if not position:
                print(f"  WARNING: Row {i} has empty position")
                valid = False
                continue
            
            # Check for duplicates
            if position in positions:
                duplicates.append(position)
            positions.add(position)
    
    print(f"  Total never positions: {len(positions)}")
    
    if duplicates:
        print(f"  WARNING: Duplicate positions found: {duplicates}")
        valid = False
    
    return valid, positions


def cross_validate(position_tags: Set[str], location_tags: Set[str], 
                  never_positions: Set[str]) -> bool:
    """Perform cross-validation between mapping files"""
    valid = True
    
    # Check for tag ID overlaps
    common_tags = position_tags.intersection(location_tags)
    if common_tags:
        print(f"  INFO: Tag IDs used for both positions and locations: {common_tags}")
        print("  This is typically OK if intentional")
    
    # Check if all tag IDs are numeric
    all_tags = position_tags.union(location_tags)
    non_numeric = [tag for tag in all_tags if tag and not tag.isdigit()]
    if non_numeric:
        print(f"  WARNING: Non-numeric tag IDs found: {non_numeric}")
        valid = False
    
    return valid


def check_sample_new_hire(mappings_dir: str = "./mappings") -> None:
    """Check how a sample new hire would be processed"""
    print("\n=== Sample New Hire Processing Check ===")
    
    # Import the mappings manager
    try:
        from mappings_manager import MappingsManager
        manager = MappingsManager(mappings_dir)
        
        # Test cases
        test_hires = [
            {
                'Legal_Firstname': 'John',
                'Legal_Lastname': 'Doe',
                'Position': 'Delivery Driver',
                'Location_Desc': 'Austin',
                'Employee_Status': 'Active'
            },
            {
                'Legal_Firstname': 'Jane',
                'Legal_Lastname': 'Smith',
                'Position': 'CFO',
                'Location_Desc': 'Lawrenceville',
                'Employee_Status': 'Active'
            },
            {
                'Legal_Firstname': 'Bob',
                'Legal_Lastname': 'Johnson',
                'Position': 'Unknown Position',
                'Location_Desc': 'Austin',
                'Employee_Status': 'Active'
            }
        ]
        
        for hire in test_hires:
            print(f"\n  Testing: {hire['Legal_Firstname']} {hire['Legal_Lastname']}")
            print(f"    Position: {hire['Position']}")
            print(f"    Location: {hire['Location_Desc']}")
            
            is_valid, error = manager.validate_new_hire(hire)
            if is_valid:
                position_tag = manager.get_position_tag(hire['Position'])
                location_tag, timezone = manager.get_location_info(hire['Location_Desc'])
                print(f"    ✓ Would be added to Samsara")
                print(f"      Position Tag: {position_tag}")
                print(f"      Location Tag: {location_tag}")
                print(f"      Timezone: {timezone}")
            else:
                print(f"    ✗ Would be skipped: {error}")
                
    except ImportError:
        print("  Could not import MappingsManager - ensure it's in the same directory")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Samsara mapping files')
    parser.add_argument(
        '--mappings-dir',
        type=str,
        default='./mappings',
        help='Directory containing mapping files'
    )
    parser.add_argument(
        '--check-sample',
        action='store_true',
        help='Check how sample new hires would be processed'
    )
    
    args = parser.parse_args()
    
    # Run validation
    print("Samsara Mappings Validation")
    print("=" * 40)
    
    valid = validate_mappings(args.mappings_dir)
    
    if args.check_sample:
        check_sample_new_hire(args.mappings_dir)
    
    print("\n" + "=" * 40)
    if valid:
        print("✓ All validations passed!")
        sys.exit(0)
    else:
        print("✗ Validation errors found - please fix the issues above")
        sys.exit(1)