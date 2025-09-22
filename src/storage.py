# src/storage.py
def get_current_score():
    # TODO: Aktuellen Score aus Datenbank/Storage holen
    return 5  # Dummy: Score 1-10

def get_latest_metrics():
    # TODO: Neueste Metriken aus Datenbank/Storage holen
    return {
        "last_update": "2025-01-22T08:00:00Z",
        "total_incidents": 42,
        "resolved_incidents": 38,
        "current_score": get_current_score()
    }