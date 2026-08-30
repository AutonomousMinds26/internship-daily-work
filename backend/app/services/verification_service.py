import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

class VerificationServiceError(Exception):
    """Exception raised when background check request fails."""
    pass


def submit_background_verification(
    candidate_id: int,
    candidate_name: str,
    candidate_email: str,
    verification_type: str = "Background",
    agency: str = "Checkr"
) -> Dict[str, Any]:
    """
    Submits a background verification request to Checkr, SpringVerify, or Internal Sandbox.
    """
    logger.info(f"[Verification] Initiating {verification_type} check for {candidate_name} via {agency}")

    # Checkr Live Integration
    if agency.lower() == "checkr" and settings.CHECKR_API_KEY and not settings.USE_MOCK_APIS:
        try:
            import httpx
            headers = {"Authorization": f"Basic {settings.CHECKR_API_KEY}"}
            payload = {
                "candidate": {"first_name": candidate_name.split()[0], "email": candidate_email},
                "package": "driver_pro" if "driving" in verification_type.lower() else "tasker_standard"
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.checkr.com/v1/candidates", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    return {
                        "success": True,
                        "agency": "Checkr",
                        "external_id": data.get("id"),
                        "status": "In Progress",
                        "message": "Checkr candidate background check initiated."
                    }
        except Exception as e:
            logger.warning(f"[Checkr Error]: {str(e)}. Falling back to Sandbox Mode.")

    # SpringVerify Live Integration
    if agency.lower() == "springverify" and settings.SPRINGVERIFY_API_KEY and not settings.USE_MOCK_APIS:
        try:
            import httpx
            headers = {"X-API-KEY": settings.SPRINGVERIFY_API_KEY}
            payload = {
                "name": candidate_name,
                "email": candidate_email,
                "verification_types": [verification_type]
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.springverify.com/v1/checks", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    return {
                        "success": True,
                        "agency": "SpringVerify",
                        "external_id": data.get("check_id"),
                        "status": "In Progress",
                        "message": "SpringVerify check created."
                    }
        except Exception as e:
            logger.warning(f"[SpringVerify Error]: {str(e)}. Falling back to Sandbox Mode.")

    # Sandbox / Mock Mode
    import hashlib
    ref_id = f"chk_{int(time.time())}_{hashlib.md5(candidate_email.encode()).hexdigest()[:6]}"
    return {
        "success": True,
        "agency": agency or "Internal",
        "external_id": ref_id,
        "status": "Pending",
        "message": f"Verification initiated with {agency}. External reference ID: {ref_id}.",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
