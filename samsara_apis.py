import os
from dotenv import load_dotenv

load_dotenv()

# Samsara API Configuration
SAMSARA_API_KEY = os.getenv('SAMSARA_API_KEY')
SAMSARA_BASE_URL = 'https://api.samsara.com'

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO', '').split(',')