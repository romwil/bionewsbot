 NotificationManager:
    """Get or create the notification manager singleton."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
