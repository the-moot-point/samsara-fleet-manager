"""
Username Utilities
Tools for managing the usernames.csv file
"""

import csv
import sys
from pathlib import Path
from typing import Set, List
import argparse

from config import SAMSARA_API_KEY, USERNAMES_FILE
from samsara_api import SamsaraAPI


def load_usernames_from_file(file_path: str = None) -> Set[str]:
    """Load usernames from CSV file"""
    usernames = set()
    file = Path(file_path or USERNAMES_FILE)
    
    if not file.exists():
        print(f"File not found: {file_path}")
        return usernames
    
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('username', '').strip().lower()
            if username:
                usernames.add(username)
    
    return usernames


def sync_usernames_from_samsara(output_file: str = None) -> int:
    """
    Sync usernames from Samsara API to local CSV file
    
    Returns:
        Number of usernames written
    """
    output_file = output_file or USERNAMES_FILE
    print("Syncing usernames from Samsara...")
    
    # Initialize API
    api = SamsaraAPI(SAMSARA_API_KEY)
    
    # Get all drivers
    try:
        drivers = api.list_drivers()
        print(f"Found {len(drivers)} drivers in Samsara")
        
        # Extract usernames
        usernames = []
        for driver in drivers:
            if driver.get('username'):
                usernames.append(driver['username'])
        
        print(f"Found {len(usernames)} drivers with usernames")
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username'])
            for username in sorted(usernames):
                writer.writerow([username])
        
        print(f"Wrote {len(usernames)} usernames to {output_file}")
        return len(usernames)
        
    except Exception as e:
        print(f"Error syncing from Samsara: {e}")
        return 0


def check_duplicates(file_path: str = None) -> List[str]:
    """Check for duplicate usernames in the file"""
    file = Path(file_path or USERNAMES_FILE)
    
    if not file.exists():
        print(f"File not found: {file}")
        return []
    
    seen = set()
    duplicates = []
    
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('username', '').strip()
            username_lower = username.lower()
            
            if username_lower in seen:
                duplicates.append(username)
            seen.add(username_lower)
    
    return duplicates


def clean_usernames_file(file_path: str = None) -> int:
    """
    Clean the usernames file by removing duplicates and empty entries
    
    Returns:
        Number of entries removed
    """
    file = Path(file_path or USERNAMES_FILE)
    
    if not file.exists():
        print(f"File not found: {file}")
        return 0
    
    # Read unique usernames
    unique_usernames = set()
    total_rows = 0
    
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            username = row.get('username', '').strip()
            if username:
                unique_usernames.add(username)
    
    # Write back unique usernames
    with open(file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username'])
        for username in sorted(unique_usernames):
            writer.writerow([username])
    
    removed = total_rows - len(unique_usernames)
    print(f"Cleaned {file}:")
    print(f"  Original entries: {total_rows}")
    print(f"  Unique entries: {len(unique_usernames)}")
    print(f"  Removed: {removed}")
    
    return removed


def add_username(username: str, file_path: str = None) -> bool:
    """
    Add a username to the file if it doesn't exist
    
    Returns:
        True if added, False if already exists
    """
    file_path = file_path or USERNAMES_FILE
    
    # Load existing usernames
    existing = load_usernames_from_file(file_path)
    
    if username.lower() in existing:
        print(f"Username '{username}' already exists")
        return False
    
    # Append to file
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username])
    
    print(f"Added username '{username}'")
    return True


def check_username(username: str, file_path: str = None) -> bool:
    """Check if a username exists in the file"""
    existing = load_usernames_from_file(file_path)
    exists = username.lower() in existing
    
    if exists:
        print(f"Username '{username}' EXISTS in the file")
    else:
        print(f"Username '{username}' is AVAILABLE")
    
    return exists


def stats(file_path: str = None) -> None:
    """Display statistics about the usernames file"""
    file = Path(file_path or USERNAMES_FILE)
    
    if not file.exists():
        print(f"File not found: {file}")
        return
    
    usernames = load_usernames_from_file(file_path)
    duplicates = check_duplicates(file_path)
    
    print(f"\nUsername File Statistics:")
    print(f"  File: {file}")
    print(f"  Total unique usernames: {len(usernames)}")
    print(f"  Duplicates found: {len(duplicates)}")
    
    if duplicates:
        print(f"\n  Duplicate usernames:")
        for dup in duplicates[:10]:  # Show first 10
            print(f"    - {dup}")
        if len(duplicates) > 10:
            print(f"    ... and {len(duplicates) - 10} more")
    
    # Analyze patterns
    print(f"\n  Username patterns:")
    patterns = {
        'single_letter': 0,
        'with_numbers': 0,
        'short': 0,
        'long': 0
    }
    
    for username in usernames:
        if len(username) <= 3:
            patterns['short'] += 1
        if len(username) >= 15:
            patterns['long'] += 1
        if any(c.isdigit() for c in username):
            patterns['with_numbers'] += 1
        if len(username) == 1:
            patterns['single_letter'] += 1
    
    print(f"    Short (≤3 chars): {patterns['short']}")
    print(f"    Long (≥15 chars): {patterns['long']}")
    print(f"    Contains numbers: {patterns['with_numbers']}")
    print(f"    Single letter: {patterns['single_letter']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Username file management utilities')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync usernames from Samsara API')
    sync_parser.add_argument('--output', default=None, help=f'Output file (default: {USERNAMES_FILE})')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean duplicates and empty entries')
    clean_parser.add_argument('--file', default=None, help=f'File to clean (default: {USERNAMES_FILE})')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if username exists')
    check_parser.add_argument('username', help='Username to check')
    check_parser.add_argument('--file', default=None, help=f'File to check (default: {USERNAMES_FILE})')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a username')
    add_parser.add_argument('username', help='Username to add')
    add_parser.add_argument('--file', default=None, help=f'File to update (default: {USERNAMES_FILE})')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show file statistics')
    stats_parser.add_argument('--file', default=None, help=f'File to analyze (default: {USERNAMES_FILE})')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'sync':
        sync_usernames_from_samsara(args.output)
    elif args.command == 'clean':
        clean_usernames_file(args.file)
    elif args.command == 'check':
        check_username(args.username, args.file)
    elif args.command == 'add':
        add_username(args.username, args.file)
    elif args.command == 'stats':
        stats(args.file)
