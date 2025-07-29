import argparse
import csv
import logging

import config
from driver_manager import DriverManager
from headcount_loader import load_headcount_data
from email_reporter import EmailReporter
from samsara_api import SamsaraAPI


def validate_csv(csv_path: str) -> None:
    """Basic CSV validation to ensure required columns exist."""
    required_columns = {
        "action",
        "payroll_id",
        "name",
        "username",
        "phone",
        "license_number",
        "license_state",
        "location_tag_id",
        "deactivation_reason",
    }
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
        sum(1 for _ in reader)


def build_email_reporter() -> EmailReporter:
    config_dict = {
        "smtp_server": config.SMTP_SERVER,
        "smtp_port": config.SMTP_PORT,
        "smtp_username": config.SMTP_USERNAME,
        "smtp_password": config.SMTP_PASSWORD,
        "from_email": config.EMAIL_FROM,
        "to_emails": config.EMAIL_TO,
        "cc_emails": config.EMAIL_CC,
        "use_tls": True,
    }
    return EmailReporter(config_dict, use_outlook=config.USE_OUTLOOK)


def main() -> int:
    parser = argparse.ArgumentParser(description="Samsara Fleet Driver Manager")
    parser.add_argument("--csv", required=True, help="CSV file with driver updates")
    parser.add_argument(
        "--headcount",
        default=config.HEADCOUNT_FILE,
        help="Path to Headcount Report.xlsx for merging update data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=config.DRY_RUN_DEFAULT,
        help="Run without making any changes",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the CSV and exit",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        validate_csv(args.csv)
    except Exception as exc:
        logging.error("CSV validation failed: %s", exc)
        return 1

    if args.validate_only:
        logging.info("CSV validated successfully")
        return 0

    api = SamsaraAPI(config.SAMSARA_API_KEY, base_url=config.SAMSARA_BASE_URL)
    manager = DriverManager(api, data_dir=config.DATA_DIR)

    headcount_map = None
    try:
        headcount_map = load_headcount_data(args.headcount)
        logging.info("Loaded headcount data from %s", args.headcount)
    except Exception as exc:
        logging.warning("Could not load headcount data: %s", exc)

    if args.dry_run:
        logging.info("Dry-run mode enabled; no changes will be made")
        return 0

    operations = manager.process_driver_updates_from_csv(
        args.csv, headcount_map=headcount_map
    )
    stats = manager.get_summary_stats()

    reporter = build_email_reporter()
    reporter.send_operations_report(operations, stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
