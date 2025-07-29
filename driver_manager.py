"""
Driver Manager
Handles business logic for driver operations using Samsara API
"""

import logging
import csv
from typing import Dict, List, Set
from datetime import datetime
import json
from pathlib import Path

from samsara_api import SamsaraAPI
from mappings_manager import MappingsManager
from config import USERNAMES_FILE

logger = logging.getLogger(__name__)


class DriverManager:
    """Manages driver operations and tracks changes"""
    
    def __init__(self, api: SamsaraAPI, mappings_manager: MappingsManager = None, data_dir: str = "./data"):
        """
        Initialize Driver Manager
        
        Args:
            api: Configured SamsaraAPI instance
            mappings_manager: MappingsManager instance for handling payroll mappings
            data_dir: Directory for storing operation logs and data
        """
        self.api = api
        self.mappings = mappings_manager or MappingsManager()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Track operations for reporting
        self.operations_log = {
            'created': [],
            'updated': [],
            'deactivated': [],
            'skipped': [],
            'errors': []
        }
        
        # Cache for existing usernames to ensure uniqueness
        self._existing_usernames: Set[str] = set()

    def _load_existing_usernames(self) -> None:
        """Load usernames from the usernames CSV file."""
        usernames_file = Path(USERNAMES_FILE)
        if not usernames_file.exists():
            return

        try:
            with open(usernames_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get("username", "").strip().lower()
                    if username:
                        self._existing_usernames.add(username)
        except Exception as exc:
            logger.error("Failed to load usernames: %s", exc)
    
    def process_driver_updates_from_csv(self, csv_file: str) -> Dict[str, List]:
        """
        Process driver updates from a CSV file
        
        Expected CSV columns:
            - action: 'create', 'update', 'deactivate'
            - payroll_id: External payroll ID
            - name: Driver name (required for create)
            - username: Username (for create)
            - phone: Phone number
            - license_number: License number
            - license_state: License state
            - location_tag_id: Location tag ID
            - deactivation_reason: Reason if deactivating
        
        Args:
            csv_file: Path to CSV file with driver updates
            
        Returns:
            Dictionary with operation results
        """
        logger.info(f"Processing driver updates from: {csv_file}")
        
        # Load existing usernames if we might be creating drivers
        self._load_existing_usernames()
        
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                action = row.get('action', '').lower()
                
                try:
                    if action == 'create':
                        self._create_driver_from_row(row)
                    elif action == 'update':
                        self._update_driver_from_row(row)
                    elif action == 'deactivate':
                        self._deactivate_driver_from_row(row)
                    else:
                        error_msg = f"Unknown action '{action}' for row: {row}"
                        logger.error(error_msg)
                        self.operations_log['errors'].append({
                            'row': row,
                            'error': error_msg,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                except Exception as e:
                    logger.error(f"Error processing row {row}: {e}")
                    self.operations_log['errors'].append({
                        'row': row,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        self._save_operations_log()
        return self.operations_log
    
    def _create_driver_from_row(self, row: Dict[str, str]) -> None:
        """Create a driver from CSV row data"""
        driver_data = {
            'name': row['name'],
            'driverActivationStatus': 'active'
        }
        
        # Add optional fields if present
        if row.get('username'):
            # Check if username is unique
            username_lower = row['username'].strip().lower()
            if username_lower in self._existing_usernames:
                logger.warning(f"Username '{row['username']}' already exists")
                self.operations_log['errors'].append({
                    'row': row,
                    'error': f"Username '{row['username']}' already exists",
                    'timestamp': datetime.utcnow().isoformat()
                })
                return
            driver_data['username'] = row['username']
        if row.get('phone'):
            driver_data['phone'] = row['phone']
        if row.get('license_number'):
            driver_data['licenseNumber'] = row['license_number']
        if row.get('license_state'):
            driver_data['licenseState'] = row['license_state']
        if row.get('payroll_id'):
            driver_data['externalIds'] = {'payrollId': row['payroll_id']}
        if row.get('location_tag_id'):
            driver_data['tagIds'] = [row['location_tag_id']]
        
        # Check if driver already exists
        if row.get('payroll_id'):
            existing = self.api.find_driver_by_external_id('payrollId', row['payroll_id'])
            if existing:
                logger.warning(f"Driver with payroll ID {row['payroll_id']} already exists")
                self.operations_log['errors'].append({
                    'row': row,
                    'error': 'Driver already exists',
                    'existing_driver_id': existing['id']
                })
                return
        
        # Create the driver
        created = self.api.create_driver(driver_data)

        # Save the username to file for future uniqueness checks
        if row.get("username"):
            self._save_username_to_file(row["username"])
        
        self.operations_log['created'].append({
            'driver_id': created['id'],
            'name': created['name'],
            'payroll_id': row.get('payroll_id'),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Created driver: {created['name']} (ID: {created['id']})")
    
    def _update_driver_from_row(self, row: Dict[str, str]) -> None:
        """Update a driver from CSV row data"""
        # Find driver by payroll ID
        if not row.get('payroll_id'):
            raise ValueError("Payroll ID required for updates")
        
        driver = self.api.find_driver_by_external_id('payrollId', row['payroll_id'])
        if not driver:
            raise ValueError(f"Driver with payroll ID {row['payroll_id']} not found")
        
        update_data = {}
        
        # Build update data from non-empty fields
        if row.get('phone'):
            update_data['phone'] = row['phone']
        if row.get('license_number'):
            update_data['licenseNumber'] = row['license_number']
        if row.get('license_state'):
            update_data['licenseState'] = row['license_state']
        if row.get('location_tag_id'):
            # Preserve existing tags and add new one
            current_tags = driver.get('tagIds', [])
            if row['location_tag_id'] not in current_tags:
                current_tags.append(row['location_tag_id'])
            update_data['tagIds'] = current_tags
        
        if update_data:
            self.api.update_driver(driver['id'], update_data)
            
            self.operations_log['updated'].append({
                'driver_id': driver['id'],
                'name': driver['name'],
                'payroll_id': row['payroll_id'],
                'fields_updated': list(update_data.keys()),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Updated driver: {driver['name']} (ID: {driver['id']})")
        else:
            logger.warning(f"No updates for driver {driver['name']}")
    
    def _deactivate_driver_from_row(self, row: Dict[str, str]) -> None:
        """Deactivate a driver from CSV row data"""
        # Find driver by payroll ID
        if not row.get('payroll_id'):
            raise ValueError("Payroll ID required for deactivation")
        
        driver = self.api.find_driver_by_external_id('payrollId', row['payroll_id'])
        if not driver:
            raise ValueError(f"Driver with payroll ID {row['payroll_id']} not found")
        
        # Check if already deactivated
        if driver.get('driverActivationStatus') == 'deactivated':
            logger.warning(f"Driver {driver['name']} is already deactivated")
            return
        
        reason = row.get('deactivation_reason', 'No reason provided')
        self.api.deactivate_driver(driver['id'], reason)
        
        self.operations_log['deactivated'].append({
            'driver_id': driver['id'],
            'name': driver['name'],
            'payroll_id': row['payroll_id'],
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Deactivated driver: {driver['name']} (ID: {driver['id']})")
    
    def sync_drivers_by_location(self, location_mappings: Dict[str, str]) -> None:
        """
        Update driver locations based on a mapping
        
        Args:
            location_mappings: Dict of payroll_id -> location_tag_id
        """
        for payroll_id, location_tag_id in location_mappings.items():
            try:
                driver = self.api.find_driver_by_external_id('payrollId', payroll_id)
                if driver:
                    self.api.update_driver_location(driver['id'], location_tag_id)
                    self.operations_log['updated'].append({
                        'driver_id': driver['id'],
                        'name': driver['name'],
                        'payroll_id': payroll_id,
                        'fields_updated': ['location'],
                        'new_location_tag': location_tag_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    logger.warning(f"Driver with payroll ID {payroll_id} not found")
                    
            except Exception as e:
                logger.error(f"Error updating location for {payroll_id}: {e}")
                self.operations_log['errors'].append({
                    'payroll_id': payroll_id,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
    
    def _save_username_to_file(self, username: str) -> None:
        """
        Append a new username to the usernames CSV file
        
        Args:
            username: Username to add to the file
        """
        usernames_file = Path(USERNAMES_FILE)
        
        try:
            # Append the username to the file
            with open(usernames_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([username])
            
            logger.debug(f"Added username '{username}' to file")
            
        except Exception as e:
            logger.error(f"Failed to save username to file: {e}")
            # Don't fail the whole operation just because we couldn't update the file
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics of operations"""
        return {
            'drivers_created': len(self.operations_log['created']),
            'drivers_updated': len(self.operations_log['updated']),
            'drivers_deactivated': len(self.operations_log['deactivated']),
            'drivers_skipped': len(self.operations_log['skipped']),
            'errors': len(self.operations_log['errors'])
        }
    
    def _save_operations_log(self) -> None:
        """Save operations log to file"""
        log_file = self.data_dir / f"operations_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump(self.operations_log, f, indent=2)
        
        logger.info(f"Operations log saved to: {log_file}")
    
    def get_recent_changes(self) -> Dict[str, List]:
        """Get all recent changes for reporting"""
        return self.operations_log


# Example CSV processing
if __name__ == "__main__":
    # Example usage
    from config import SAMSARA_API_KEY
    
    # Initialize API and manager
    api = SamsaraAPI(SAMSARA_API_KEY)
    manager = DriverManager(api)
    
    # Process updates from CSV
    # results = manager.process_driver_updates_from_csv('driver_updates.csv')
    
    # Print summary
    # stats = manager.get_summary_stats()
    # print(f"Created: {stats['drivers_created']}")
    # print(f"Updated: {stats['drivers_updated']}")
    # print(f"Deactivated: {stats['drivers_deactivated']}")
    # print(f"Errors: {stats['errors']}")