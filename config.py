"""
Configuration settings for Samsara Driver Management System
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Samsara API Configuration
SAMSARA_API_KEY = os.getenv('SAMSARA_API_KEY')
SAMSARA_BASE_URL = os.getenv('SAMSARA_BASE_URL', 'https://api.samsara.com')

# Email Configuration
USE_OUTLOOK = os.getenv('USE_OUTLOOK', 'True').lower() == 'true'  # Set to True to use Outlook COM

# SMTP Configuration (used if USE_OUTLOOK is False)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.office365.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')  # Optional
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Optional

# Email addresses
EMAIL_FROM = os.getenv('EMAIL_FROM', 'fleet-management@company.com')
EMAIL_TO = os.getenv('EMAIL_TO', '').split(',')  # Comma-separated list
EMAIL_CC = os.getenv('EMAIL_CC', '').split(',') if os.getenv('EMAIL_CC') else []

# File paths
INPUT_DIR = os.getenv('INPUT_DIR', './input')
DATA_DIR = os.getenv('DATA_DIR', './data')
LOG_DIR = os.getenv('LOG_DIR', './logs')
MAPPINGS_DIR = os.getenv('MAPPINGS_DIR', './mappings')
USERNAMES_FILE = os.getenv('USERNAMES_FILE', './usernames.csv')

# Operational settings
DRY_RUN_DEFAULT = os.getenv('DRY_RUN_DEFAULT', 'False').lower() == 'true'
VALIDATE_BEFORE_PROCESS = os.getenv('VALIDATE_BEFORE_PROCESS', 'True').lower() == 'true'

# Location tag mappings (optional)
# Format: "location_name:tag_id,location_name2:tag_id2"
LOCATION_TAG_MAPPINGS = {}
if os.getenv('LOCATION_TAG_MAPPINGS'):
    for mapping in os.getenv('LOCATION_TAG_MAPPINGS').split(','):
        if ':' in mapping:
            name, tag_id = mapping.split(':', 1)
            LOCATION_TAG_MAPPINGS[name.strip()] = tag_id.strip()

# Validate required configuration
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not SAMSARA_API_KEY:
        errors.append("SAMSARA_API_KEY is required")
    
    if not EMAIL_FROM:
        errors.append("EMAIL_FROM is required")
    
    if not EMAIL_TO or EMAIL_TO == ['']:
        errors.append("EMAIL_TO is required")
    
    if not USE_OUTLOOK:
        if not SMTP_SERVER:
            errors.append("SMTP_SERVER is required when not using Outlook")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check your .env file")
        return False
    
    return True


# Run validation when module is imported
if not validate_config():
    import sys
    sys.exit(1)