import requests
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LinkedInOAuthClient:
    """
    LinkedIn OAuth-based API client supporting access tokens, refresh tokens, and ID tokens.
    """

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.refresh_token = os.getenv("LINKEDIN_REFRESH_TOKEN")
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        # Updated to use the REST endpoint for versioned APIs
        self.base_url = "https://api.linkedin.com"

        # Session for connection pooling and consistency
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Setup default headers and session configuration."""
        self.session.headers.update(
            {
                "User-Agent": "LinkedIn-MCP-Tool/1.0",
                "Accept": "application/json",
                "Content-Type": "text/plain",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "X-Restli-Protocol-Version",  # Latest version as of July 2025
            }
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with current access token."""
        if not self.access_token:
            raise ValueError("No access token available. Please authenticate first.")

        return {"Authorization": f"Bearer {self.access_token}"}

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        Returns True if successful, False otherwise.
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.error("Missing refresh token or client credentials")
            return False

        token_url = "https://www.linkedin.com/oauth/v2/accessToken"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                # Update refresh token if provided
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]

                logger.info("Access token refreshed successfully")
                return True
            else:
                logger.error(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to LinkedIn API.
        Automatically handles token refresh if needed.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {**self.session.headers, **self._get_auth_headers()}

        if "headers" in kwargs:
            headers.update(kwargs["headers"])

        kwargs["headers"] = headers

        try:
            response = self.session.request(method, url, **kwargs)

            print(response.text)

            # If unauthorized, try to refresh token once
            if response.status_code == 401:
                logger.info("Access token expired, attempting refresh...")
                if self.refresh_access_token():
                    # Retry with new token
                    headers = {**self.session.headers, **self._get_auth_headers()}
                    if "headers" in kwargs:
                        headers.update(kwargs["headers"])
                    kwargs["headers"] = headers
                    response = self.session.request(method, url, **kwargs)
                else:
                    raise Exception("Failed to refresh access token")

            return response

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_profile(self, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get the authenticated user's profile using LinkedIn API v2."""
        # Use the correct LinkedIn API v2 endpoint for profile
        endpoint = "/v2/userinfo"
        if fields:
            endpoint += f"?fields={fields}"

        try:
            # For profile endpoint, we need to use the v2 base URL
            v2_url = f"https://api.linkedin.com{endpoint}"
            headers = {**self.session.headers, **self._get_auth_headers()}

            response = self.session.request("GET", v2_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception(
                    "Profile access forbidden. Please ensure your LinkedIn app has the 'r_basicprofile' or 'profile' scope."
                )
            elif e.response.status_code == 401:
                raise Exception(
                    "Unauthorized. Please check your access token or refresh it."
                )
            else:
                raise Exception(
                    f"Profile API error: {e.response.status_code} - {e.response.text}"
                )


# Global client instance
_client = None


def get_client() -> LinkedInOAuthClient:
    """Get or create the LinkedIn OAuth client instance."""
    global _client
    if _client is None:
        _client = LinkedInOAuthClient()
    return _client
