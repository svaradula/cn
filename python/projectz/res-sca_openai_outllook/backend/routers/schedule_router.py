"""
schedule_router.py — Microsoft Graph API integration for interview scheduling.

OAuth2 permission type: DELEGATED (on-behalf-of signed-in user)
----------------------------------------------------------------
This app uses the Authorization Code flow with Delegated permissions.
The HR user signs in with their own Microsoft account, and the app
acts on their behalf to:
  - Send email from their Outlook account
  - Create events on their calendar
  - Generate Teams meetings in their name

This is DIFFERENT from Application permissions (used by daemons/services
that run without any signed-in user). Application permissions require
different Azure setup and a different auth flow (client credentials).

Required Azure setup
--------------------
1. App Registration → Authentication:
   - Add platform: Web
   - Redirect URI: http://localhost:8000/api/auth/callback
   - Check "ID tokens" under Implicit grant (optional but helpful for debug)

2. API Permissions → Add DELEGATED permissions (NOT Application):
   - Calendars.ReadWrite
   - OnlineMeetings.ReadWrite
   - Mail.Send
   - User.Read
   - offline_access  (for refresh tokens — auto-included by MSAL)

3. Click "Grant admin consent for [org]" — all must show green tick + Yes.

4. Certificates & Secrets → New client secret → copy value to .env
"""
import logging
import os
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────

TENANT_ID     = os.environ.get("AZURE_TENANT_ID", "")
CLIENT_ID     = os.environ.get("AZURE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
REDIRECT_URI  = os.environ.get("AZURE_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
FRONTEND_URL  = os.environ.get("FRONTEND_URL", "http://localhost:5173")

AUTHORITY  = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# ── IMPORTANT: these must be DELEGATED permissions in Azure Portal ────────────
# offline_access is required to receive a refresh token so the session
# persists without the user having to log in on every request.
SCOPES = [
    "Calendars.ReadWrite",
    "OnlineMeetings.ReadWrite",
    "Mail.Send",
    "User.Read",
    "offline_access",
]

# In-memory token store — replace with Redis/DB in production
_token_store: dict[str, str] = {}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    from_email:    str
    to_email:      str
    cc_emails:     List[str] = []
    subject:       str
    body:          str
    interview_dt:  str        # ISO 8601 e.g. "2025-09-15T14:00:00"
    timezone:      str = "UTC"
    duration_min:  int = 60
    include_teams: bool = True
    candidate_name: str = ""
    role_name:     str = ""

class ScheduleResponse(BaseModel):
    success:       bool
    teams_link:    Optional[str] = None
    event_id:      Optional[str] = None
    calendar_link: Optional[str] = None
    message:       str


# ── OAuth2 endpoints ──────────────────────────────────────────────────────────

@router.get("/auth/admin-consent-url")
async def get_admin_consent_url():
    """
    Returns the admin consent URL that a Global Admin must visit once
    to pre-approve the app for all users in the organisation.
    Use this when individual users see 'Approval required' screens.
    """
    if not CLIENT_ID or not TENANT_ID:
        raise HTTPException(status_code=500, detail="Azure credentials not configured.")
    url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/adminconsent"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return {"admin_consent_url": url, "instructions": "A Global Admin of your organisation must open this URL and click Accept."}


@router.get("/auth/login")
async def ms_login():
    """
    Redirect to Microsoft login page.
    Uses Authorization Code flow (Delegated permissions, on-behalf-of signed-in user).
    """
    if not CLIENT_ID or not TENANT_ID:
        raise HTTPException(
            status_code=500,
            detail="Azure credentials missing. Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET in .env",
        )

    scope_str = " ".join(SCOPES)
    import urllib.parse
    auth_url = (
        f"{AUTHORITY}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
        f"&scope={urllib.parse.quote(scope_str, safe='')}"
        f"&response_mode=query"
        f"&prompt=select_account"
    )
    logger.info("Redirecting to Microsoft OAuth2 login")
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback")
async def ms_callback(code: str = None, error: str = None, error_description: str = None):
    """
    Handle the OAuth2 callback from Microsoft.

    Microsoft sends either:
      ?code=xxx       — success, exchange for token
      ?error=xxx      — user denied or admin consent required
    """
    # ── Handle errors returned by Microsoft ───────────────────────────────────
    if error:
        logger.error("OAuth2 error: %s — %s", error, error_description)

        # "access_denied" with "AADSTS65004" = user cancelled consent
        # "consent_required" = admin consent not yet granted
        if error in ("access_denied", "consent_required"):
            return RedirectResponse(
                url=f"{FRONTEND_URL}?ms_auth=error&reason=consent_required"
            )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?ms_auth=error&reason={error}"
        )

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received from Microsoft.")

    # ── Exchange code for access token ────────────────────────────────────────
    token_url = f"{AUTHORITY}/oauth2/v2.0/token"
    payload = {
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
        "scope":         " ".join(SCOPES),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=payload)

    if resp.status_code != 200:
        err_data = resp.json()
        logger.error("Token exchange failed: %s", err_data)

        # Common failure: admin consent not granted
        # error code AADSTS90094 or AADSTS65001
        err_code = err_data.get("error", "")
        err_desc = err_data.get("error_description", "")
        if "AADSTS90094" in err_desc or "AADSTS65001" in err_desc or "admin_consent" in err_desc:
            return RedirectResponse(
                url=f"{FRONTEND_URL}?ms_auth=error&reason=admin_consent_required"
            )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?ms_auth=error&reason=token_exchange_failed"
        )

    tokens = resp.json()
    access_token  = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    _token_store["access_token"]  = access_token
    _token_store["refresh_token"] = refresh_token or ""

    # ── Fetch the signed-in user's email ─────────────────────────────────────
    async with httpx.AsyncClient() as client:
        me_resp = await client.get(
            f"{GRAPH_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if me_resp.status_code == 200:
        me_data = me_resp.json()
        user_email = me_data.get("mail") or me_data.get("userPrincipalName", "")
        _token_store["user_email"] = user_email
        logger.info("OAuth2 login successful: %s", user_email)
    else:
        user_email = ""
        logger.warning("Could not fetch /me: %s", me_resp.text)

    return RedirectResponse(
        url=f"{FRONTEND_URL}?ms_auth=success&user_email={user_email}"
    )


@router.get("/auth/status")
async def auth_status():
    """Check if HR user is authenticated with Microsoft."""
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
    Three Graph API calls:
      1. POST /me/onlineMeetings  → Teams meeting link
      2. POST /me/events          → Calendar event with attendees
      3. POST /me/sendMail        → Outlook email to candidate
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

    from datetime import datetime, timedelta

    try:
        start_dt = datetime.fromisoformat(payload.interview_dt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview_dt. Use ISO 8601 format.")

    end_dt = start_dt + timedelta(minutes=payload.duration_min)

    teams_link:    Optional[str] = None
    event_id:      Optional[str] = None
    calendar_link: Optional[str] = None

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── Step 1: Teams meeting ─────────────────────────────────────────────
        if payload.include_teams:
            teams_resp = await client.post(
                f"{GRAPH_BASE}/me/onlineMeetings",
                headers=headers,
                json={
                    "startDateTime": start_dt.isoformat(),
                    "endDateTime":   end_dt.isoformat(),
                    "subject":       payload.subject,
                },
            )
            if teams_resp.status_code in (200, 201):
                teams_link = teams_resp.json().get("joinWebUrl")
                logger.info("Teams meeting created")
            else:
                # 401 = token expired, 403 = missing OnlineMeetings.ReadWrite scope
                logger.warning(
                    "Teams meeting failed (status %d): %s",
                    teams_resp.status_code, teams_resp.text[:300],
                )

        # ── Step 2: Build body with Teams link ────────────────────────────────
        teams_html = ""
        if teams_link:
            teams_html = f"""
            <div style="margin:16px 0;padding:12px 16px;background:#f3f0ff;
                        border-left:4px solid #7B2391;border-radius:4px;">
              <p style="margin:0 0 6px;font-weight:600;color:#7B2391;">
                📹 Microsoft Teams Meeting
              </p>
              <a href="{teams_link}" style="color:#1B3A8C;word-break:break-all;">
                {teams_link}
              </a>
            </div>"""

        full_body = payload.body + teams_html

        # ── Step 3: Calendar event ────────────────────────────────────────────
        attendees = [{"emailAddress": {"address": payload.to_email}, "type": "required"}]
        for cc in payload.cc_emails:
            if cc.strip():
                attendees.append({
                    "emailAddress": {"address": cc.strip()},
                    "type": "optional",
                })

        event_payload = {
            "subject":   payload.subject,
            "body":      {"contentType": "HTML", "content": full_body},
            "start":     {"dateTime": start_dt.isoformat(), "timeZone": payload.timezone},
            "end":       {"dateTime": end_dt.isoformat(),   "timeZone": payload.timezone},
            "attendees": attendees,
            "isOnlineMeeting": bool(teams_link),
        }

        event_resp = await client.post(
            f"{GRAPH_BASE}/me/events",
            headers=headers,
            json=event_payload,
        )
        if event_resp.status_code in (200, 201):
            event_data    = event_resp.json()
            event_id      = event_data.get("id")
            calendar_link = event_data.get("webLink")
            logger.info("Calendar event created: %s", event_id)
        else:
            logger.error("Calendar event failed (status %d): %s",
                         event_resp.status_code, event_resp.text[:300])
            raise HTTPException(
                status_code=502,
                detail=f"Failed to create calendar event: {event_resp.text[:300]}",
            )

        # ── Step 4: Send email ────────────────────────────────────────────────
        mail_resp = await client.post(
            f"{GRAPH_BASE}/me/sendMail",
            headers=headers,
            json={
                "message": {
                    "subject": payload.subject,
                    "body":    {"contentType": "HTML", "content": full_body},
                    "toRecipients": [{"emailAddress": {"address": payload.to_email}}],
                    "ccRecipients": [
                        {"emailAddress": {"address": cc.strip()}}
                        for cc in payload.cc_emails if cc.strip()
                    ],
                },
                "saveToSentItems": True,
            },
        )
        if mail_resp.status_code == 202:
            logger.info("Email sent to %s", payload.to_email)
        else:
            logger.error("Email send failed (status %d): %s",
                         mail_resp.status_code, mail_resp.text[:300])
            raise HTTPException(
                status_code=502,
                detail=f"Calendar event created but email failed: {mail_resp.text[:300]}",
            )

    return ScheduleResponse(
        success=True,
        teams_link=teams_link,
        event_id=event_id,
        calendar_link=calendar_link,
        message=(
            "Interview scheduled successfully."
            + (" Teams invite sent." if teams_link else "")
        ),
    )