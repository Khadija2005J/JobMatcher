import requests
from typing import Dict, Any

GOOGLE_CAL_EVENTS = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
OUTLOOK_EVENTS = "https://graph.microsoft.com/v1.0/me/events"

def create_google_event(access_token: str, event: Dict[str, Any]):
    """Create an event in the user's primary Google Calendar.

    access_token: OAuth2 access token with calendar scope.
    event: dict following Google Calendar events resource minimal fields.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(GOOGLE_CAL_EVENTS, json=event, headers=headers, timeout=10)
    try:
        resp.raise_for_status()
    except Exception as e:
        return {"ok": False, "status_code": resp.status_code, "error": resp.text}
    return {"ok": True, "data": resp.json()}

def create_outlook_event(access_token: str, event: Dict[str, Any]):
    """Create an event in the user's Outlook/Graph mailbox.

    event: dict following Microsoft Graph create event payload.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(OUTLOOK_EVENTS, json=event, headers=headers, timeout=10)
    try:
        resp.raise_for_status()
    except Exception as e:
        return {"ok": False, "status_code": resp.status_code, "error": resp.text}
    return {"ok": True, "data": resp.json()}
