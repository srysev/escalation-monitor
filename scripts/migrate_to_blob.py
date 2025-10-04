#!/usr/bin/env python3
"""
Migration script to upload existing reports to Vercel Blob Storage.

This script migrates local JSON reports from src/reports/ to Vercel Blob Storage.
It reuses the _save_to_blob() and _get_from_blob() functions from src/storage.py.

Usage:
    python scripts/migrate_to_blob.py [--dry-run] [--verify] [--start-date YYYY-MM-DD] [--target-env ENV]

Examples:
    # Dry-run to see what would be migrated to dev
    python scripts/migrate_to_blob.py --dry-run

    # Migrate all reports from 2025-09-30 onwards to production
    python scripts/migrate_to_blob.py --start-date 2025-09-30 --target-env prod

    # Migrate to dev with verification
    python scripts/migrate_to_blob.py --verify --target-env dev
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local (Vercel standard) or .env
load_dotenv('.env.local')  # Try Vercel's .env.local first
load_dotenv()              # Fallback to .env if it exists

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import _save_to_blob, _get_from_blob, BLOB_TOKEN, REPORTS_DIR


def parse_date_from_filename(filename: str) -> datetime:
    """Extract date from report filename (e.g., '2025-09-30.json' -> datetime)."""
    date_str = filename.replace('.json', '')
    return datetime.strptime(date_str, '%Y-%m-%d')


def get_reports_to_migrate(start_date: datetime) -> list[Path]:
    """
    Get list of report files to migrate, filtered by start_date.

    Args:
        start_date: Only include reports from this date onwards

    Returns:
        List of Path objects for JSON report files
    """
    reports = []

    if not REPORTS_DIR.exists():
        print(f"Error: Reports directory not found: {REPORTS_DIR}")
        return reports

    for file_path in sorted(REPORTS_DIR.glob("*.json")):
        # Skip files with special suffixes (e.g., 2025-09-30-good.json)
        if len(file_path.stem.split('-')) > 3:
            print(f"Skipping non-standard filename: {file_path.name}")
            continue

        try:
            file_date = parse_date_from_filename(file_path.name)
            if file_date >= start_date:
                reports.append(file_path)
        except ValueError:
            print(f"Warning: Could not parse date from {file_path.name}, skipping")
            continue

    return reports


def migrate_report(file_path: Path, dry_run: bool = False, verify: bool = False) -> bool:
    """
    Migrate a single report to Vercel Blob Storage.

    Args:
        file_path: Path to the JSON report file
        dry_run: If True, only simulate the migration
        verify: If True, verify the upload by reading back from blob

    Returns:
        bool: True if successful, False otherwise
    """
    date_str = file_path.stem  # e.g., "2025-09-30"
    pathname = f"reports/{date_str}.json"

    # Read the report data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ✗ Error reading {file_path.name}: {e}")
        return False

    if dry_run:
        print(f"  [DRY-RUN] Would upload {file_path.name} to blob://{pathname}")
        return True

    # Upload to blob
    success = _save_to_blob(pathname, data)

    if success:
        print(f"  ✓ Uploaded {file_path.name} to blob://{pathname}")

        # Optional verification
        if verify:
            retrieved_data = _get_from_blob(pathname)
            if retrieved_data == data:
                print(f"    ✓ Verification successful")
            else:
                print(f"    ✗ Verification failed: Data mismatch")
                return False
    else:
        print(f"  ✗ Failed to upload {file_path.name}")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Migrate local reports to Vercel Blob Storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without actually uploading'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify each upload by reading back from blob storage'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2025-09-30',
        help='Start date for migration (format: YYYY-MM-DD, default: 2025-09-30)'
    )
    parser.add_argument(
        '--target-env',
        type=str,
        choices=['dev', 'prod'],
        default='dev',
        help='Target environment for migration (default: dev)'
    )

    args = parser.parse_args()

    # Parse start date
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    except ValueError:
        print(f"Error: Invalid date format: {args.start_date}")
        print("Please use YYYY-MM-DD format (e.g., 2025-09-30)")
        sys.exit(1)

    # Check environment
    print("=" * 60)
    print("Vercel Blob Migration Script")
    print("=" * 60)

    if not BLOB_TOKEN:
        print("\nError: BLOB_READ_WRITE_TOKEN not found in environment")
        print("Please set up your environment variables:")
        print("  1. Run: vercel env pull")
        print("  2. Or set manually: export BLOB_READ_WRITE_TOKEN=your_token")
        sys.exit(1)

    # Set target environment
    os.environ['ENVIRONMENT'] = args.target_env
    print(f"\nTarget environment: {args.target_env}")
    if args.target_env == 'prod':
        print("⚠️  WARNING: Migrating to PRODUCTION environment!")
    print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
    print(f"Dry-run mode: {args.dry_run}")
    print(f"Verify uploads: {args.verify}")
    print(f"Source directory: {REPORTS_DIR}")
    print()

    # Get reports to migrate
    reports = get_reports_to_migrate(start_date)

    if not reports:
        print("No reports found to migrate.")
        sys.exit(0)

    print(f"Found {len(reports)} report(s) to migrate:\n")

    # Migrate each report
    success_count = 0
    failed_count = 0

    for file_path in reports:
        if migrate_report(file_path, dry_run=args.dry_run, verify=args.verify):
            success_count += 1
        else:
            failed_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total reports: {len(reports)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")

    if args.dry_run:
        print("\nThis was a dry-run. No actual uploads were performed.")
        print("Run without --dry-run to perform the migration.")

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == '__main__':
    main()
