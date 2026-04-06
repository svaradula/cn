"""
schedule_router.py — Microsoft Graph API integration for interview scheduling.

Handles:
  1. POST /api/schedule-interview  — create Teams meeting + calendar event + send email
  2. GET  /api/auth/login          — redirect to Microsoft OAuth2 login
  3. GET  /api/auth/callback       — handle OAuth2 callback, return access token

Microsoft Graph API flow
------------------------
                    ┌─────────────────────────────┐
  Browser           │   Azure App Registration    │
     │              │   - Client ID               │
     │  1. Login    │   - Client Secret           │
     │─────────────►│   - Redirect URI            │
     │              └──────────────┬──────────────┘
     │                             │  2. Auth code
     │◄────────────────────────────┘
     │  3. Exchange code for token
     │─────────────────────────────► /api/auth/callback
     │                               │  4. Access token stored
     │  5. Schedule interview        │
     │──────────────────────────────►│
     │                               │  6. Graph API calls:
     │                               │     a. Create Teams meeting
     │                               │     b. Create calendar event
     │                               │     c. Send email via Outlook
     │◄──────────────────────────────│
     │  7. Success + invite details

Required Azure setup (see README for steps):
  - App Registration at portal.azure.com
  - API Permissions: Calendars.ReadWrite, OnlineMeetings.ReadWrite, Mail.Send, User.Read
  - Redirect URI: http://localhost:8000/api/auth/callback
"""
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Microsoft OAuth2 + Graph config ──────────────────────────────────────────

TENANT_ID     = os.environ.get("AZURE_TENANT_ID", "")
CLIENT_ID     = os.environ.get("AZURE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
REDIRECT_URI  = os.environ.get("AZURE_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
FRONTEND_URL  = os.environ.get("FRONTEND_URL", "http://localhost:5173")

AUTHORITY     = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_BASE    = "https://graph.microsoft.com/v1.0"

SCOPES = [
    "Calendars.ReadWrite",
    "OnlineMeetings.ReadWrite",
    "Mail.Send",
    "User.Read",
]

# In-memory token store (per worker process).
# In production use Redis or a database.
_token_store: dict[str, str] = {}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    from_email:   str
    to_email:     str
    cc_emails:    List[str] = []
    subject:      str
    body:         str                   # HTML body from rich-text editor
    interview_dt: str                   # ISO 8601, e.g. "2025-09-15T14:00:00+05:30"
    timezone:     str = "UTC"
    duration_min: int = 60
    include_teams: bool = True
    candidate_name: str = ""
    role_name:    str = ""

class ScheduleResponse(BaseModel):
    success:       bool
    teams_link:    Optional[str] = None
    event_id:      Optional[str] = None
    calendar_link: Optional[str] = None
    message:       str


# ── OAuth2 endpoints ──────────────────────────────────────────────────────────

@router.get("/auth/login")
async def ms_login():
    """
    Redirect the browser to Microsoft's OAuth2 consent page.
    The user logs in with their Microsoft 365 / Outlook account.
    """
    if not CLIENT_ID or not TENANT_ID:
        raise HTTPException(
            status_code=500,
            detail=(
                "Azure credentials not configured. "
                "Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET in .env"
            ),
        )

    scope_str = "%20".join(SCOPES + ["offline_access"])
    auth_url = (
        f"{AUTHORITY}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope_str}"
        f"&response_mode=query"
    )
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback")
async def ms_callback(code: str, request: Request):
    """
    Exchange the OAuth2 authorization code for an access token.
    Stores it in memory and redirects the frontend with a success flag.
    """
    token_url = f"{AUTHORITY}/oauth2/v2.0/token"
    payload = {
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
        "scope":         " ".join(SCOPES + ["offline_access"]),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=payload)

    if resp.status_code != 200:
        logger.error("Token exchange failed: %s", resp.text)
        raise HTTPException(status_code=400, detail="OAuth2 token exchange failed.")

    tokens = resp.json()
    access_token = tokens.get("access_token")
    _token_store["access_token"] = access_token

    # Fetch user's own email to show in the UI
    async with httpx.AsyncClient() as client:
        me = await client.get(
            f"{GRAPH_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    user_email = me.json().get("mail") or me.json().get("userPrincipalName", "")
    _token_store["user_email"] = user_email

    logger.info("OAuth2 login successful for: %s", user_email)
    return RedirectResponse(
        url=f"{FRONTEND_URL}?ms_auth=success&user_email={user_email}"
    )


@router.get("/auth/status")
async def auth_status():
    """Check whether the user is currently authenticated with Microsoft."""
    token = _token_store.get("access_token")
    email = _token_store.get("user_email", "")
    return {"authenticated": bool(token), "user_email": email}


@router.post("/auth/logout")
async def logout():
    _token_store.clear()
    return {"success": True}


# ── Schedule interview ────────────────────────────────────────────────────────

@router.post("/schedule-interview", response_model=ScheduleResponse)
async def schedule_interview(payload: ScheduleRequest):
    """
    Full interview scheduling flow:
      1. Create a Teams online meeting (if include_teams=True)
      2. Create a calendar event with attendees
      3. Send confirmation email via Outlook

    All three Graph API calls run with the stored OAuth2 token.
    """
    token = _token_store.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated with Microsoft. Please connect your Outlook account first.",
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    teams_link: Optional[str] = None
    event_id:   Optional[str] = None

    # Parse the interview datetime
    try:
        interview_dt = datetime.fromisoformat(payload.interview_dt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview_dt format. Use ISO 8601.")

    end_dt = interview_dt.replace(
        hour=interview_dt.hour + (payload.duration_min // 60),
        minute=(interview_dt.minute + payload.duration_min) % 60,
    )

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── Step 1: Create Teams meeting ──────────────────────────────────────
        if payload.include_teams:
            teams_payload = {
                "startDateTime": interview_dt.isoformat(),
                "endDateTime":   end_dt.isoformat(),
                "subject":       payload.subject,
            }
            teams_resp = await client.post(
                f"{GRAPH_BASE}/me/onlineMeetings",
                headers=headers,
                json=teams_payload,
            )
            if teams_resp.status_code in (200, 201):
                teams_link = teams_resp.json().get("joinWebUrl")
                logger.info("Teams meeting created: %s", teams_link)
            else:
                logger.warning("Teams meeting creation failed: %s", teams_resp.text)

        # ── Step 2: Build email body with Teams link ──────────────────────────
        teams_section = ""
        if teams_link:
            teams_section = f"""
            <div style="margin:16px 0;padding:12px 16px;background:#f3f0ff;border-left:4px solid #7B2391;border-radius:4px;">
              <p style="margin:0 0 6px;font-weight:600;color:#7B2391;">📹 Microsoft Teams Meeting</p>
              <a href="{teams_link}" style="color:#1B3A8C;word-break:break-all;">{teams_link}</a>
            </div>"""

        full_body = payload.body + teams_section

        # ── Step 3: Create calendar event with attendees ──────────────────────
        attendees = [{"emailAddress": {"address": payload.to_email}, "type": "required"}]
        for cc in payload.cc_emails:
            if cc.strip():
                attendees.append({"emailAddress": {"address": cc.strip()}, "type": "optional"})

        event_payload = {
            "subject":   payload.subject,
            "body":      {"contentType": "HTML", "content": full_body},
            "start":     {"dateTime": interview_dt.isoformat(), "timeZone": payload.timezone},
            "end":       {"dateTime": end_dt.isoformat(),       "timeZone": payload.timezone},
            "attendees": attendees,
            "isOnlineMeeting": payload.include_teams,
            "onlineMeetingProvider": "teamsForBusiness" if payload.include_teams else None,
        }

        event_resp = await client.post(
            f"{GRAPH_BASE}/me/events",
            headers=headers,
            json={k: v for k, v in event_payload.items() if v is not None},
        )
        if event_resp.status_code in (200, 201):
            event_data  = event_resp.json()
            event_id    = event_data.get("id")
            calendar_link = event_data.get("webLink")
            logger.info("Calendar event created: %s", event_id)
        else:
            logger.error("Calendar event creation failed: %s", event_resp.text)
            raise HTTPException(
                status_code=502,
                detail=f"Failed to create calendar event: {event_resp.text}",
            )

        # ── Step 4: Send email via Outlook ────────────────────────────────────
        to_recipients = [{"emailAddress": {"address": payload.to_email}}]
        cc_recipients = [
            {"emailAddress": {"address": cc.strip()}}
            for cc in payload.cc_emails if cc.strip()
        ]

        mail_payload = {
            "message": {
                "subject": payload.subject,
                "body":    {"contentType": "HTML", "content": full_body},
                "toRecipients": to_recipients,
                "ccRecipients": cc_recipients,
            },
            "saveToSentItems": True,
        }

        mail_resp = await client.post(
            f"{GRAPH_BASE}/me/sendMail",
            headers=headers,
            json=mail_payload,
        )
        if mail_resp.status_code == 202:
            logger.info("Email sent to %s", payload.to_email)
        else:
            logger.error("Email send failed: %s", mail_resp.text)
            raise HTTPException(
                status_code=502,
                detail=f"Calendar event created but email failed: {mail_resp.text}",
            )

    return ScheduleResponse(
        success=True,
        teams_link=teams_link,
        event_id=event_id,
        calendar_link=calendar_link,
        message=(
            f"Interview scheduled successfully."
            + (" Teams invite sent." if teams_link else "")
        ),
    )