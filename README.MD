# Samsara Fleet Driver Management System

An automated system for managing driver records in Samsara Fleet Management via API, designed to run daily through Windows Task Scheduler.

## Features

- **Create new drivers** in Samsara from CSV data
- **Update driver information** (phone, license, location tags)
- **Deactivate drivers** with reasons
- **Email reports** of all operations performed
- **Error handling** and detailed logging
- **Dry-run mode** for testing

## Project Structure

```
samsara-fleet-manager/
├── config.py              # Configuration settings
├── samsara_api.py         # Samsara API wrapper
├── driver_manager.py      # Driver operations logic
├── email_reporter.py      # Email report generation
├── main.py               # Main entry point for Task Scheduler
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment configuration
├── README.md             # This file
├── input/                # Input CSV files directory
│   └── driver_updates.csv
├── data/                 # Operation logs directory
├── logs/                 # Application logs directory
└── driver_updates_example.csv  # Example CSV format
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If using Outlook for email:
```bash
pip install pywin32
```

### 2. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your configuration:
   - **SAMSARA_API_KEY**: Your Samsara API key
   - **EMAIL_TO**: Comma-separated list of report recipients
   - **USE_OUTLOOK**: Set to `True` for Outlook, `False` for SMTP

### 3. Prepare Input Data

Create a CSV file in the `input/` directory with driver updates. See `driver_updates_example.csv` for the format.

CSV columns:
- **action**: `create`, `update`, or `deactivate`
- **payroll_id**: External payroll ID (required for update/deactivate)
- **name**: Full name (required for create)
- **username**: Samsara login username
- **phone**: Phone number
- **license_number**: Driver's license number
- **license_state**: License state (2-letter code)
- **location_tag_id**: Samsara tag ID for location
- **deactivation_reason**: Reason for deactivation

## Using with Claude Code

1. **Create the project structure** as shown above
2. **Add all the Python files** to your project directory
3. **Include any existing code** or Samsara documentation
4. **Run Claude Code** pointing to this directory:
   ```bash
   claude-code /path/to/samsara-fleet-manager
   ```

Claude Code can help you:
- Modify the API integration
- Add new features
- Debug issues
- Customize email reports
- Extend functionality

## Running the System

### Manual Run
```bash
python main.py --csv input/driver_updates.csv
```

### Dry Run (Test Mode)
```bash
python main.py --csv input/driver_updates.csv --dry-run
```

### Validate CSV Only
```bash
python main.py --csv input/driver_updates.csv --validate-only
```

## Windows Task Scheduler Setup

1. Open Task Scheduler
2. Create Basic Task:
   - Name: "Samsara Driver Update"
   - Trigger: Daily at your preferred time
   - Action: Start a program

3. Configure the Action:
   - **Program/script**: `C:\Python39\python.exe` (your Python path)
   - **Arguments**: `main.py --csv input/driver_updates.csv`
   - **Start in**: `C:\path\to\samsara-fleet-manager`

4. Additional Settings:
   - Run whether user is logged on or not
   - Run with highest privileges
   - Configure for Windows 10/11

## Email Reports

The system sends HTML email reports containing:
- Summary statistics
- List of created drivers
- List of updated drivers
- List of deactivated drivers
- Any errors encountered

Reports are sent only when operations are performed.

## Logging

Logs are stored in the `logs/` directory with daily rotation:
- Format: `samsara_driver_sync_YYYYMMDD.log`
- Includes timestamps, operation details, and errors

## Error Handling

- API errors are logged and included in email reports
- CSV validation errors prevent processing
- Critical errors trigger error notification emails
- All operations are logged for audit trail

## Troubleshooting

### Common Issues

1. **"SAMSARA_API_KEY is required"**
   - Ensure `.env` file exists and contains your API key

2. **Email not sending with Outlook**
   - Ensure Outlook is installed and configured
   - Check that `pywin32` is installed
   - Try running with administrator privileges

3. **CSV validation errors**
   - Check column names match exactly
   - Ensure required fields are populated
   - Use the `--validate-only` flag to test

### Debug Mode

For detailed debugging, modify the logging level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Security Notes

- Never commit `.env` file to version control
- Store API keys securely
- Restrict access to log and data directories
- Use service accounts for automated runs

## Support

For Samsara API documentation: https://developers.samsara.com/docs/introduction

For issues with this system:
1. Check the logs in `logs/` directory
2. Validate your CSV format
3. Test with `--dry-run` mode
4. Verify API key permissions in Samsara