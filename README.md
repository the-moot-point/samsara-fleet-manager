# Samsara Fleet Driver Management System

An automated system for managing driver records in Samsara Fleet Management via API, designed to run daily through Windows Task Scheduler.

## Features

- **Create new drivers** in Samsara from CSV data
- **Update driver information** (phone, license, location tags)
- **Sync updates with Headcount data** for phone, location, and email
- **Deactivate drivers** with reasons
- **Email reports** of all operations performed
- **Error handling** and detailed logging
- **Dry-run mode** for testing

## Project Structure

```
samsara-fleet-manager/
├── main.py                  # Entry point when running manually
├── driver_manager.py        # Core driver logic
├── email_reporter.py        # Email reporting helpers
├── username_utils.py        # Username utilities
├── config.py                # Configuration helpers
├── validate_mappings_script.py
├── positions.csv            # Mapping files
├── locations.csv
├── never_positions.csv
├── usernames.csv
├── input/                   # Input CSV files directory
│   ├── new_hires_example.csv
│   └── NEW_HIRES_example.xlsx
├── Headcount Report.xlsx    # Example spreadsheet for verifying totals
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Developer dependencies
├── .env.example             # Example environment configuration
├── README.md                # Project documentation
├── tests/                   # Unit tests
└── pytest.ini
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

If using Outlook for email:
```bash
pip install pywin32
```

### 2. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env  # use `copy` on Windows
   ```

2. Edit `.env` and add your configuration:
   - **SAMSARA_API_KEY**: Your Samsara API key
   - **EMAIL_TO**: Comma-separated list of report recipients
   - **USE_OUTLOOK**: Set to `True` for Outlook, `False` for SMTP

### 3. Prepare Input Data

Create a CSV file in the `input/` directory with new-hire details. See `new_hires_example.csv` for the format.

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

The repository also includes **Headcount Report.xlsx**, which provides a
snapshot of current driver counts. You can use it as a reference to verify
that the automated results match your internal records.

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
python main.py --csv input/new_hires_example.csv \
  --headcount "Headcount Report.xlsx"
```

### Dry Run (Test Mode)
```bash
python main.py --csv input/new_hires_example.csv \
  --headcount "Headcount Report.xlsx" --dry-run
```

### Validate CSV Only
```bash
python main.py --csv input/new_hires_example.csv \
  --headcount "Headcount Report.xlsx" --validate-only
```

## Windows Task Scheduler Setup

1. Open Task Scheduler
2. Create Basic Task:
   - Name: "Samsara Driver Update"
   - Trigger: Daily at your preferred time
   - Action: Start a program

3. Configure the Action:
   - **Program/script**: `C:\Python39\python.exe` (your Python path)
   - **Arguments**: `main.py --csv input/new_hires_example.csv --headcount "Headcount Report.xlsx"`
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

If problems persist, open an issue or contact the repository maintainer for help.
