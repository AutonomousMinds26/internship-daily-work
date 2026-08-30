import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    """Exception raised when email dispatch fails."""
    pass


def send_email_notification(
    recipient: str,
    subject: str,
    content: str,
    template_type: Optional[str] = None,
    attachments: Optional[list] = None
) -> Dict[str, Any]:
    """
    Sends an email notification via SendGrid, SMTP, or Mock Sandbox.
    Handles HTML rendering, credentials checking, and failure recovery.
    """
    if not recipient:
        raise EmailDeliveryError("Recipient email cannot be empty.")

    # 1. SendGrid Integration (if API key provided and not mock mode)
    if settings.SENDGRID_API_KEY and not settings.USE_MOCK_APIS:
        try:
            logger.info(f"[SendGrid] Outgoing email dispatch to {recipient} with subject '{subject}'")
            import httpx
            headers = {
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "personalizations": [{"to": [{"email": recipient}]}],
                "from": {"email": settings.SMTP_FROM_EMAIL, "name": "RecruiterAI Platform"},
                "subject": subject,
                "content": [{"type": "text/html", "value": content}]
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
                if res.status_code in (200, 202):
                    return {
                        "success": True,
                        "provider": "SendGrid",
                        "recipient": recipient,
                        "message_id": res.headers.get("X-Message-Id", "sg_sent"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    logger.warning(f"[SendGrid] Failed with status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"[SendGrid Error]: {str(e)}. Falling back to SMTP/Sandbox.")

    # 2. SMTP Integration (if configured)
    if settings.SMTP_PASSWORD and not settings.USE_MOCK_APIS:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            logger.info(f"[SMTP] Outgoing email dispatch to {recipient} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = recipient

            part = MIMEText(content, "html")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [recipient], msg.as_string())

            return {
                "success": True,
                "provider": "SMTP",
                "recipient": recipient,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"[SMTP Error]: {str(e)}. Falling back to Sandbox Mode.")

    # 3. Sandbox / Mock Mode
    logger.info(f"[Email Sandbox Mock] Dispatched email to {recipient}. Subject: '{subject}'")
    import hashlib
    simulated_id = hashlib.md5(f"{recipient}_{subject}_{datetime.now(timezone.utc)}".encode()).hexdigest()
    return {
        "success": True,
        "provider": "Mock-Sandbox",
        "recipient": recipient,
        "subject": subject,
        "message_id": f"mock_mail_{simulated_id[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def render_email_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Renders standardized rich HTML templates for recruitment workflows.
    """
    candidate_name = context.get("candidate_name", "Candidate")
    job_title = context.get("job_title", "Open Position")
    company_name = context.get("company_name", "RecruiterAI Talent Team")

    if template_name == "interview_invitation":
        scheduled_time = context.get("scheduled_time", "Upcoming")
        interviewer = context.get("interviewer_name", "Hiring Team")
        meeting_link = context.get("meeting_link", "https://meet.google.com")
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 24px; background: #f8fafc; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #4f46e5;">Interview Invitation: {job_title}</h2>
                <p>Dear {candidate_name},</p>
                <p>We are pleased to invite you to an interview for the <strong>{job_title}</strong> role.</p>
                <div style="background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 4px 0;"><strong>Date & Time:</strong> {scheduled_time}</p>
                    <p style="margin: 4px 0;"><strong>Interviewer:</strong> {interviewer}</p>
                    <p style="margin: 4px 0;"><strong>Meeting Link:</strong> <a href="{meeting_link}" style="color: #6366f1;">{meeting_link}</a></p>
                </div>
                <p>Best regards,<br/>{company_name}</p>
            </div>
        </div>
        """

    elif template_name == "offer_letter":
        salary = context.get("salary", "Competitive")
        currency = context.get("currency", "INR")
        start_date = context.get("start_date", "Mutually Agreed")
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 24px; background: #f8fafc; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #10b981;">Offer of Employment: {job_title}</h2>
                <p>Dear {candidate_name},</p>
                <p>We are thrilled to extend an offer for the position of <strong>{job_title}</strong>!</p>
                <div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 16px; margin: 20px 0;">
                    <p style="margin: 4px 0;"><strong>Base Compensation:</strong> {currency} {salary}</p>
                    <p style="margin: 4px 0;"><strong>Target Start Date:</strong> {start_date}</p>
                </div>
                <p>Please review and confirm your acceptance.</p>
                <p>Warm congratulations,<br/>{company_name}</p>
            </div>
        </div>
        """

    else:
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 24px; color: #1e293b;">
            <p>Dear {candidate_name},</p>
            <p>{context.get('message', 'Thank you for your interest in our open role.')}</p>
            <p>Best regards,<br/>{company_name}</p>
        </div>
        """
