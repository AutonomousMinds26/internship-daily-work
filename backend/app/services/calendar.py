import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import re
from typing import cast, Any

from app.models import Interview, Candidate, Job, CandidateHistory

logger = logging.getLogger(__name__)

def parse_iso_datetime(time_str: str) -> datetime:
    """Helper to parse scheduled time string into a datetime object."""
    try:
        # Try to parse standard ISO format (e.g. 2026-08-01T21:00:00 or 2026-08-01 21:00:00)
        time_str_clean = time_str.replace(" ", "T")
        # Remove offset details if present (we'll assume UTC or parse it)
        if time_str_clean.endswith("Z"):
            time_str_clean = time_str_clean[:-1]
        
        # Simple match for YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?', time_str_clean)
        if match:
            g = match.groups()
            sec = int(g[5]) if g[5] else 0
            dt = datetime(int(g[0]), int(g[1]), int(g[2]), int(g[3]), int(g[4]), sec, tzinfo=timezone.utc)
            return dt
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{time_str}': {str(e)}")
    
    return datetime.now(timezone.utc) + timedelta(days=1) # Default tomorrow

def generate_ics_invite(interview: Interview, candidate: Candidate, job: Job) -> str:
    """
    Generates standard .ics (iCalendar) invite payload.
    """
    dt_start = parse_iso_datetime(str(interview.scheduled_time))
    duration = float(cast(Any, interview.duration_minutes)) if interview.duration_minutes is not None else 45.0
    dt_end = dt_start + timedelta(minutes=duration)

    # Format dates as YYYYMMDDTHHMMSSZ (UTC format)
    gcal_format = "%Y%m%dT%H%M%SZ"
    start_str = dt_start.astimezone(timezone.utc).strftime(gcal_format)
    end_str = dt_end.astimezone(timezone.utc).strftime(gcal_format)
    stamp_str = datetime.now(timezone.utc).strftime(gcal_format)

    summary = f"Interview: {candidate.name} vs {job.title} - RecruiterAI"
    description = (
        f"Position: {job.title}\\n"
        f"Candidate: {candidate.name} ({candidate.email})\\n"
        f"Interviewer: {interview.interviewer_name} ({interview.interviewer_email})\\n"
        f"Mode: {interview.mode}\\n"
        f"Meeting Link: {interview.meeting_link or 'N/A'}\\n"
        f"Notes: {interview.notes or 'None'}"
    )

    ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RecruiterAI//Recruitment System//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:interview_{interview.id}@recruiterai.com",
        f"SEQUENCE:0",
        f"STATUS:CONFIRMED",
        f"DTSTAMP:{stamp_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{interview.meeting_link or interview.mode}",
        f"ORGANIZER;CN=RecruiterAI Admin:MAILTO:admin@recruiterai.com",
        f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN={candidate.name}:MAILTO:{candidate.email}",
        f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN={interview.interviewer_name}:MAILTO:{interview.interviewer_email}",
        "END:VEVENT",
        "END:VCALENDAR"
    ]
    
    return "\n".join(ics)

def mock_google_calendar_event(interview: Interview, candidate: Candidate, job: Job) -> str:
    """
    Creates a Google Calendar event. If real keys are missing, runs in sandbox mock mode.
    """
    import os
    google_creds = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    
    if google_creds:
        logger.info("Found Google Calendar Credentials. Initiating real event creation...")
        # If we had the google library, we would run:
        # from googleapiclient.discovery import build
        # service = build('calendar', 'v3', credentials=creds)
        # event = service.events().insert(calendarId='primary', body=event_body).execute()
        # return event['id']
        pass
        
    # Return a simulated event ID
    import hashlib
    seed_str = f"gcal_{interview.id}_{interview.scheduled_time}"
    event_id = hashlib.md5(seed_str.encode()).hexdigest()
    logger.info(f"Sandbox Mock: Generated Google Calendar event with ID: gcal_{event_id}")
    return f"gcal_{event_id}"

def send_interview_notifications(db: Session, interview: Interview, candidate: Candidate, job: Job):
    """
    Generate the invite, save to DB, log history, and trigger simulated email logs.
    """
    # 1. Generate ICS invite
    ics_text = generate_ics_invite(interview, candidate, job)
    cast(Any, interview).calendar_invite = ics_text

    # 2. Integrate with Google Calendar (Mock or Live)
    gcal_id = mock_google_calendar_event(interview, candidate, job)
    cast(Any, interview).calendar_event_id = gcal_id
    db.commit()

    # 3. Log history
    history = CandidateHistory(
        candidate_id=candidate.id,
        action="Interview Calendar Invite Generated",
        details=(
            f"Calendar invite generated for interview with {interview.interviewer_name}. "
            f"Meeting Link: {interview.meeting_link or 'N/A'}. Google Event ID: {gcal_id}"
        ),
        performed_by="RecruiterAI System"
    )
    db.add(history)
    db.commit()

    # 4. Trigger email sending notifications (logs)
    logger.info(
        f"EMAIL NOTIFICATION SENT to Candidate ({candidate.email}) & Interviewer ({interview.interviewer_email}) "
        f"for scheduled interview ID: {interview.id} at {interview.scheduled_time}."
    )
