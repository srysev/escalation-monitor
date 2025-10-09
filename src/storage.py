# src/storage.py
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
BLOB_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")

# Reports directory path (for local storage)
REPORTS_DIR = Path(__file__).parent / "reports"

# Vercel Blob API configuration
BLOB_API_BASE = "https://blob.vercel-storage.com"

def _save_to_blob(pathname: str, data: Dict[str, Any]) -> bool:
    """
    Save data to Vercel Blob Storage.

    Args:
        pathname: Path in blob storage (e.g. "reports/2025-01-15.json")
        data: Data to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not BLOB_TOKEN:
            print("BLOB_READ_WRITE_TOKEN not found, falling back to local storage")
            return False

        # Prepare JSON content
        content = json.dumps(data, indent=2, ensure_ascii=False)

        # Upload to Blob Storage
        # x-add-random-suffix: 0 = Use exact pathname without random hash
        # x-allow-overwrite: 1 = Allow overwriting existing files (like local filesystem)
        with httpx.Client() as client:
            response = client.put(
                f"{BLOB_API_BASE}/{pathname}",
                content=content.encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {BLOB_TOKEN}",
                    "x-content-type": "application/json",
                    "x-add-random-suffix": "0",
                    "x-allow-overwrite": "1",
                },
                timeout=30.0
            )
            response.raise_for_status()

        return True

    except Exception as e:
        print(f"Error saving to Blob Storage: {e}")
        return False


def _save_to_local(date_str: str, data: Dict[str, Any]) -> bool:
    """
    Save data to local filesystem.

    Args:
        date_str: Date string (YYYY-MM-DD)
        data: Data to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure reports directory exists
        REPORTS_DIR.mkdir(exist_ok=True)

        # Save to file
        file_path = REPORTS_DIR / f"{date_str}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error saving to local storage: {e}")
        return False


def save_escalation_report(escalation_result: Dict[str, Any]) -> bool:
    """
    Save escalation report to JSON file with format YYYY-MM-DD.json.
    Storage backend determined by ENVIRONMENT variable:
    - "local" (or unset): Local filesystem
    - "dev" or "prod": Vercel Blob Storage with fallback to local

    Args:
        escalation_result: Result from calculate_escalation_score()

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get current date in UTC
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%Y-%m-%d")
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Prepare report data
        report_data = {
            "date": date_str,
            "timestamp": timestamp_str,
            "escalation_result": escalation_result
        }

        # Determine storage backend
        if ENVIRONMENT in ["dev", "prod"]:
            pathname = f"reports/{date_str}.json"
            success = _save_to_blob(pathname, report_data)

            # Fallback to local if blob fails
            if not success:
                print(f"Blob storage failed, falling back to local storage")
                return _save_to_local(date_str, report_data)

            return True
        else:
            # Local storage
            return _save_to_local(date_str, report_data)

    except Exception as e:
        print(f"Error saving escalation report: {e}")
        return False

def _get_from_blob(pathname: str) -> Optional[Dict[str, Any]]:
    """
    Get data from Vercel Blob Storage using List API with prefix filter.

    This function uses a 2-step process:
    1. List blobs with pathname as prefix to find the download URL
    2. Download the actual data using the returned URL

    Args:
        pathname: Path in blob storage (e.g. "reports/2025-01-15.json")

    Returns:
        Dict with data or None if not found/error
    """
    try:
        if not BLOB_TOKEN:
            print("BLOB_READ_WRITE_TOKEN not found, falling back to local storage")
            return None

        with httpx.Client() as client:
            # Step 1: List blobs with prefix (without .json extension for broader match)
            prefix = pathname.replace('.json', '')

            list_response = client.get(
                f"{BLOB_API_BASE}/",
                params={"prefix": prefix},
                headers={
                    "Authorization": f"Bearer {BLOB_TOKEN}",
                },
                timeout=30.0
            )

            if list_response.status_code == 404:
                return None

            list_response.raise_for_status()
            list_data = list_response.json()

            # Step 2: Find matching blob
            blobs = list_data.get('blobs', [])
            if not blobs:
                return None

            # Use first match (should be exactly one with our naming scheme)
            blob = blobs[0]
            download_url = blob['url']

            # Step 3: Download actual data using the blob's URL
            data_response = client.get(download_url, timeout=30.0)
            data_response.raise_for_status()
            return data_response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        print(f"Error getting from Blob Storage: {e}")
        return None
    except Exception as e:
        print(f"Error getting from Blob Storage: {e}")
        return None


def _get_from_local(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Get data from local filesystem.

    Args:
        date_str: Date string (YYYY-MM-DD)

    Returns:
        Dict with data or None if not found/error
    """
    try:
        file_path = REPORTS_DIR / f"{date_str}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception as e:
        print(f"Error reading from local storage: {e}")
        return None


def get_latest_report(max_days_back: int = 7) -> Optional[Dict[str, Any]]:
    """
    Get most recent escalation report (today or up to max_days_back days ago).

    Searches backwards from today up to max_days_back days for the newest available report.
    Adds metadata to the report:
    - is_today: bool - Whether the report is from today
    - age_days: int - How many days old the report is (0 = today)

    Args:
        max_days_back: Maximum number of days to search backwards (default: 7)

    Returns:
        Dict with report data + metadata or None if no report found
    """
    try:
        today = datetime.now(timezone.utc).date()

        for days_back in range(max_days_back + 1):
            check_date = today - timedelta(days=days_back)
            date_str = check_date.strftime("%Y-%m-%d")

            report = get_report_by_date(date_str)
            if report:
                # Add metadata about report age
                report["is_today"] = (days_back == 0)
                report["age_days"] = days_back
                return report

        return None

    except Exception as e:
        print(f"Error reading latest report: {e}")
        return None


def get_today_report() -> Optional[Dict[str, Any]]:
    """
    Get today's escalation report with fallback to recent days.

    If today's report is not available, falls back to reports from previous days
    (up to 7 days back). The returned report includes metadata indicating its age.

    Returns:
        Dict with report data + metadata (is_today, age_days) or None if not found/error
    """
    return get_latest_report(max_days_back=7)

def get_report_by_date(date: str) -> Optional[Dict[str, Any]]:
    """
    Get escalation report for specific date.
    Storage backend determined by ENVIRONMENT variable:
    - "local" (or unset): Local filesystem
    - "dev" or "prod": Vercel Blob Storage with fallback to local

    Args:
        date: Date string in format YYYY-MM-DD

    Returns:
        Dict with report data or None if not found/error
    """
    try:
        # Determine storage backend
        if ENVIRONMENT in ["dev", "prod"]:
            pathname = f"reports/{date}.json"
            data = _get_from_blob(pathname)

            # Fallback to local if blob fails
            if data is None:
                data = _get_from_local(date)

            return data
        else:
            # Local storage
            return _get_from_local(date)

    except Exception as e:
        print(f"Error reading report for date {date}: {e}")
        return None