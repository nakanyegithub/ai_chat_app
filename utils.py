from datetime import datetime, timezone
import re

def get_current_time():
    return datetime.now(timezone.utc)

def format_timestamp(timestamp):
    if not timestamp:
        return ''
    now = datetime.now(timezone.utc)
    diff = now - timestamp
    if diff.days > 0:
        return timestamp.strftime('%d.%m.%Y')
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "just now"

def validate_username(username):
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores and hyphens"
    return True, ""

def validate_password(password):
    if not password or len(password) < 3:
        return False, "Password must be at least 3 characters"
    return True, ""

def truncate_text(text, max_length=50):
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
