# src/storage.py
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Reports directory path
REPORTS_DIR = Path(__file__).parent / "reports"

def save_escalation_report(escalation_result: Dict[str, Any]) -> bool:
    """
    Save escalation report to JSON file with format YYYY-MM-DD.json.

    Args:
        escalation_result: Result from calculate_escalation_score()

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure reports directory exists
        REPORTS_DIR.mkdir(exist_ok=True)

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

        # Save to file
        file_path = REPORTS_DIR / f"{date_str}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error saving escalation report: {e}")
        return False

def get_today_report() -> Optional[Dict[str, Any]]:
    """
    Get today's escalation report.

    Returns:
        Dict with report data or None if not found/error
    """
    try:
        # Get current date in UTC
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return get_report_by_date(today_str)

    except Exception as e:
        print(f"Error reading today's report: {e}")
        return None

def get_report_by_date(date: str) -> Optional[Dict[str, Any]]:
    """
    Get escalation report for specific date.

    Args:
        date: Date string in format YYYY-MM-DD

    Returns:
        Dict with report data or None if not found/error
    """
    try:
        file_path = REPORTS_DIR / f"{date}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception as e:
        print(f"Error reading report for date {date}: {e}")
        return None