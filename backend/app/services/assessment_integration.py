import os
import time
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- Custom Integration Exceptions ---

class APIIntegrationError(Exception):
    """Base exception for API integrations."""
    pass

class APIAuthenticationError(APIIntegrationError):
    """Exception raised when authentication fails (401/403)."""
    pass

class APIUnavailableError(APIIntegrationError):
    """Exception raised when the API is down or unavailable (5xx/Network issues)."""
    pass

class APIResponseError(APIIntegrationError):
    """Exception raised when response is invalid or represents a user/data request error (4xx)."""
    pass

class APITimeoutError(APIIntegrationError):
    """Exception raised when requests time out."""
    pass


# --- Base API Client with Logging, Retry, and Timeout ---

class BaseExternalClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        auth_header: Dict[str, str],
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        use_mock: Optional[bool] = None
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.auth_header = auth_header
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Determine if we should run in mock mode
        if use_mock is not None:
            self.use_mock = use_mock
        else:
            # Mock if requested via env, or if URL/Auth credentials are empty/placeholders
            env_mock = os.getenv("USE_MOCK_APIS", "true").lower() in ("true", "1", "yes")
            is_placeholder_url = "example.com" in base_url or not base_url
            is_placeholder_auth = not auth_header or any("placeholder" in v.lower() for v in auth_header.values())
            self.use_mock = env_mock or is_placeholder_url or is_placeholder_auth

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes HTTP requests with retries, timeout management, auth handling, and logging.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self.auth_header, "Content-Type": "application/json"}

        attempt = 0
        delay = 1.0

        while attempt < self.max_retries:
            attempt += 1
            try:
                logger.info(
                    f"[{self.name}] Outgoing request: {method} {url} "
                    f"(Attempt {attempt}/{self.max_retries})"
                )
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(
                        method,
                        url,
                        json=json_data,
                        params=params,
                        headers=headers
                    )
                
                # Log response code
                logger.info(f"[{self.name}] Response status: {response.status_code}")

                # 1. Handle Auth errors
                if response.status_code in (401, 403):
                    logger.error(f"[{self.name}] Authentication failed: {response.text}")
                    raise APIAuthenticationError(
                        f"[{self.name}] Auth failure: status {response.status_code}"
                    )

                # 2. Handle Server errors (Temporary unavailable)
                if response.status_code >= 500:
                    logger.warning(f"[{self.name}] Service unavailable: status {response.status_code}")
                    raise APIUnavailableError(
                        f"[{self.name}] Service returned status {response.status_code}"
                    )

                # 3. Handle Client / Request errors
                if response.status_code >= 400:
                    logger.error(f"[{self.name}] Request error: status {response.status_code} - {response.text}")
                    raise APIResponseError(
                        f"[{self.name}] Request error status {response.status_code}: {response.text}"
                    )

                # 4. Parse JSON
                try:
                    return response.json()
                except Exception as e:
                    logger.error(f"[{self.name}] Failed to parse JSON response: {response.text}")
                    raise APIResponseError(
                        f"[{self.name}] Response is not valid JSON: {str(e)}"
                    )

            except httpx.TimeoutException as e:
                logger.warning(f"[{self.name}] Timeout on attempt {attempt}: {str(e)}")
                if attempt == self.max_retries:
                    raise APITimeoutError(
                        f"[{self.name}] Request timed out after {self.max_retries} attempts: {str(e)}"
                    )

            except httpx.NetworkError as e:
                logger.warning(f"[{self.name}] Network error on attempt {attempt}: {str(e)}")
                if attempt == self.max_retries:
                    raise APIUnavailableError(
                        f"[{self.name}] Network connection failed after {self.max_retries} attempts"
                    )

            except (APIUnavailableError) as e:
                if attempt == self.max_retries:
                    raise

            # Retry delay with backoff factor
            logger.info(f"[{self.name}] Retrying request in {delay:.2f} seconds...")
            time.sleep(delay)
            delay *= self.backoff_factor

        raise APIUnavailableError(f"[{self.name}] Request failed after max retries.")


# --- Concrete Clients (Greenhouse, Lever, HackerRank, Codility, Mettl) ---

class GreenhouseClient(BaseExternalClient):
    def __init__(self, base_url: str = "", api_key: str = "", use_mock: Optional[bool] = None):
        auth_header = {"Authorization": f"Basic {api_key}"} if api_key else {"Authorization": "Basic placeholder"}
        super().__init__(
            name="Greenhouse",
            base_url=base_url or "https://api.greenhouse.io/v1",
            auth_header=auth_header,
            use_mock=use_mock
        )

    def import_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Imports candidate into Greenhouse ATS."""
        if self.use_mock:
            logger.info("[Greenhouse MOCK] Sourcing/importing candidate.")
            # Trigger intentional mock failures if specific testing emails are used
            email = candidate_data.get("email", "")
            if "timeout" in email:
                raise APITimeoutError("[Greenhouse MOCK] Simulated Timeout")
            if "auth_fail" in email:
                raise APIAuthenticationError("[Greenhouse MOCK] Simulated Auth Failure")
            if "unavailable" in email:
                raise APIUnavailableError("[Greenhouse MOCK] Simulated Service Unavailable")
            if "invalid" in email:
                raise APIResponseError("[Greenhouse MOCK] Simulated Invalid Response")
                
            return {
                "success": True,
                "external_id": f"gh_cand_{int(time.time())}",
                "status": "Applied",
                "provider": "Greenhouse",
                "message": "Candidate imported successfully into Greenhouse."
            }
        return self._request("POST", "/candidates", json_data=candidate_data)


class LeverClient(BaseExternalClient):
    def __init__(self, base_url: str = "", api_key: str = "", use_mock: Optional[bool] = None):
        auth_header = {"Authorization": f"Bearer {api_key}"} if api_key else {"Authorization": "Bearer placeholder"}
        super().__init__(
            name="Lever",
            base_url=base_url or "https://api.lever.co/v1",
            auth_header=auth_header,
            use_mock=use_mock
        )

    def import_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates/sourcing a candidate in Lever."""
        if self.use_mock:
            logger.info("[Lever MOCK] Importing candidate.")
            return {
                "success": True,
                "external_id": f"lever_cand_{int(time.time())}",
                "status": "Lead",
                "provider": "Lever",
                "message": "Candidate profile successfully created in Lever."
            }
        return self._request("POST", "/candidates", json_data=candidate_data)


class HackerRankClient(BaseExternalClient):
    def __init__(self, base_url: str = "", api_key: str = "", use_mock: Optional[bool] = None):
        auth_header = {"X-HackerRank-API-Key": api_key} if api_key else {"X-HackerRank-API-Key": "placeholder"}
        super().__init__(
            name="HackerRank",
            base_url=base_url or "https://api.hackerrank.com/v1",
            auth_header=auth_header,
            use_mock=use_mock
        )

    def invite_candidate(self, email: str, test_name: str) -> Dict[str, Any]:
        """Invites a candidate to a HackerRank test."""
        if self.use_mock:
            logger.info(f"[HackerRank MOCK] Sending test invite to {email} for {test_name}")
            return {
                "success": True,
                "assessment_id": f"hr_test_{int(time.time())}",
                "invite_url": f"https://hackerrank.com/test-invite/hr_test_{int(time.time())}",
                "status": "Pending"
            }
        return self._request("POST", "/tests/invites", json_data={"email": email, "test_name": test_name})

    def get_test_results(self, assessment_id: str) -> Dict[str, Any]:
        """Gets evaluation score report for an assessment."""
        if self.use_mock:
            logger.info(f"[HackerRank MOCK] Getting results for {assessment_id}")
            return {
                "status": "Completed",
                "score": 85.0,
                "max_score": 100.0,
                "report_url": f"https://hackerrank.com/reports/{assessment_id}"
            }
        return self._request("GET", f"/tests/results/{assessment_id}")


class CodilityClient(BaseExternalClient):
    def __init__(self, base_url: str = "", api_key: str = "", use_mock: Optional[bool] = None):
        auth_header = {"X-Codility-API-Key": api_key} if api_key else {"X-Codility-API-Key": "placeholder"}
        super().__init__(
            name="Codility",
            base_url=base_url or "https://api.codility.com/v1",
            auth_header=auth_header,
            use_mock=use_mock
        )

    def invite_candidate(self, email: str, test_name: str) -> Dict[str, Any]:
        """Invites candidate to a Codility coding session."""
        if self.use_mock:
            logger.info(f"[Codility MOCK] Sending test invite to {email} for {test_name}")
            return {
                "success": True,
                "assessment_id": f"codility_test_{int(time.time())}",
                "invite_url": f"https://codility.com/test-invite/codility_test_{int(time.time())}",
                "status": "Pending"
            }
        return self._request("POST", "/invitations", json_data={"email": email, "test_name": test_name})

    def get_test_results(self, assessment_id: str) -> Dict[str, Any]:
        """Gets evaluation results for a test session."""
        if self.use_mock:
            logger.info(f"[Codility MOCK] Getting results for {assessment_id}")
            return {
                "status": "Completed",
                "score": 90.0,
                "max_score": 100.0,
                "report_url": f"https://codility.com/reports/{assessment_id}"
            }
        return self._request("GET", f"/invitations/{assessment_id}/results")


class MettlClient(BaseExternalClient):
    def __init__(self, base_url: str = "", api_key: str = "", use_mock: Optional[bool] = None):
        auth_header = {"X-Mettl-API-Key": api_key} if api_key else {"X-Mettl-API-Key": "placeholder"}
        super().__init__(
            name="MercerMettl",
            base_url=base_url or "https://api.mettl.com/v1",
            auth_header=auth_header,
            use_mock=use_mock
        )

    def invite_candidate(self, email: str, test_name: str) -> Dict[str, Any]:
        """Invites a candidate to a Mercer Mettl assessment."""
        if self.use_mock:
            logger.info(f"[Mercer Mettl MOCK] Sending test invite to {email} for {test_name}")
            return {
                "success": True,
                "assessment_id": f"mettl_test_{int(time.time())}",
                "invite_url": f"https://mettl.com/test-invite/mettl_test_{int(time.time())}",
                "status": "Pending"
            }
        return self._request("POST", "/assessments/invite", json_data={"email": email, "test_name": test_name})

    def get_test_results(self, assessment_id: str) -> Dict[str, Any]:
        """Retrieves test result scores."""
        if self.use_mock:
            logger.info(f"[Mercer Mettl MOCK] Getting results for {assessment_id}")
            return {
                "status": "Completed",
                "score": 78.0,
                "max_score": 100.0,
                "report_url": f"https://mettl.com/reports/{assessment_id}"
            }
        return self._request("GET", f"/assessments/results/{assessment_id}")


# --- Unified Manager / Facade ---

class AssessmentIntegrationManager:
    """
    Facade coordinating calls to Greenhouse, Lever, HackerRank, Codility, and Mettl clients.
    """
    def __init__(self, use_mock: Optional[bool] = None):
        self.greenhouse = GreenhouseClient(use_mock=use_mock)
        self.lever = LeverClient(use_mock=use_mock)
        self.hackerrank = HackerRankClient(use_mock=use_mock)
        self.codility = CodilityClient(use_mock=use_mock)
        self.mettl = MettlClient(use_mock=use_mock)

    def get_client_by_provider(self, provider: str) -> BaseExternalClient:
        provider_lower = provider.lower()
        if "greenhouse" in provider_lower:
            return self.greenhouse
        elif "lever" in provider_lower:
            return self.lever
        elif "hackerrank" in provider_lower:
            return self.hackerrank
        elif "codility" in provider_lower:
            return self.codility
        elif "mettl" in provider_lower or "mercer" in provider_lower:
            return self.mettl
        else:
            raise ValueError(f"Unknown external provider: {provider}")
