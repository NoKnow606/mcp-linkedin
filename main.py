import logging
from os import access

from fastmcp import FastMCP, Context
import requests
import os
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)

mcp = FastMCP("mcp-linkedin", port=3333, host='0.0.0.0')


class LinkedInOAuthClient:
    """
    LinkedIn OAuth-based API client supporting access tokens, refresh tokens, and ID tokens.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, access_token: Optional[str]=None, refresh_token: Optional[str]=None):
        self.access_token = access_token  or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.getenv("LINKEDIN_REFRESH_TOKEN")
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
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

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
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





# Regular functions for testing and direct usage
def _get_profile_info(ctx: Context) -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Returns:
        String containing formatted profile information or error message
    """
    try:
        headers = {}
        if ctx and hasattr(ctx, 'request_context') and ctx.request_context:
            headers_raw = ctx.request_context.request.get("headers", {})

            # Convert headers from list of tuples to dictionary
            if isinstance(headers_raw, list):
                headers = {key.decode() if isinstance(key, bytes) else key:
                               value.decode() if isinstance(value, bytes) else value
                           for key, value in headers_raw}
            else:
                headers = headers_raw

        client_id = headers.get("linkedin_client_id")
        client_secret = headers.get("linkedin_client_secret")
        access_token = headers.get("linkedin_access_token")

        if client_id and client_secret and access_token:
            logger.info("Creating post on LinkedIn")
        else:
            return f"Error creating post: Miss client_id or client_secret or access_token"

        client = LinkedInOAuthClient(client_id=client_id, client_secret=client_secret, access_token=access_token)

        profile = client.get_profile()

        result = "LinkedIn Profile Information:\n"
        for key, value in profile.items():
            result += f"{key}: {value}\n"

        return result

    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return f"Error retrieving profile: {str(e)}"


# def _refresh_token() -> str:
#     """
#     Manually refresh the LinkedIn access token using the refresh token.
#
#     Returns:
#         String indicating success or failure of token refresh
#     """
#     try:
#         success = client.refresh_access_token()
#
#         if success:
#             return "Access token refreshed successfully."
#         else:
#             return "Failed to refresh access token. Check your refresh token and client credentials."
#
#     except Exception as e:
#         logger.error(f"Error refreshing token: {e}")
#         return f"Error refreshing token: {str(e)}"


def _create_post(
    ctx: Context,
    commentary: str,
    visibility: str = "PUBLIC",
    feed_distribution: str = "MAIN_FEED",
) -> str:
    """
    Create a post on LinkedIn using the REST API.

    Args:
        commentary: The text content of the post
        visibility: Visibility of the post (PUBLIC, CONNECTIONS, LOGGED_IN)
        feed_distribution: Feed distribution setting (MAIN_FEED, NONE)

    Returns:
        String containing the post creation result or error message
    """
    try:
        headers = {}
        if ctx and hasattr(ctx, 'request_context') and ctx.request_context:
            headers_raw = ctx.request_context.request.get("headers", {})

            # Convert headers from list of tuples to dictionary
            if isinstance(headers_raw, list):
                headers = {key.decode() if isinstance(key, bytes) else key:
                               value.decode() if isinstance(value, bytes) else value
                           for key, value in headers_raw}
            else:
                headers = headers_raw

        client_id = headers.get("linkedin_client_id")
        client_secret = headers.get("linkedin_client_secret")
        refresh_token = headers.get("linkedin_refresh_token")


        if client_id and client_secret and refresh_token:
            logger.info("Creating post on LinkedIn")
        else:
            return f"Error creating post: Miss client_id or client_secret or refresh_token"



        client = LinkedInOAuthClient(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

        client.refresh_access_token()

        profile = client.get_profile()

        author_id = profile.get("sub")

        author = "urn:li:person:" + author_id

        # Create the post payload according to LinkedIn REST API spec
        post_data = {
            "author": author,
            "commentary": commentary,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": feed_distribution,
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": True,
        }

        print(post_data)

        # Make the API call to create the post using the REST API
        response = client.make_request(
            "POST",
            "/v2/posts",
            json=post_data,
        )

        response.raise_for_status()

        return f"Post created successfully!"

    except Exception as e:
        logger.error(f"Error creating post: {e}")
        # If it's an HTTP error, try to get more details
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.text
                logger.error(f"API Error Response: {error_details}")
                
                if e.response.status_code == 403:
                    return f"Error creating post: Permission denied (403).\n" \
                           f"This usually means your LinkedIn app doesn't have the required permissions.\n" \
                           f"Required permissions: 'w_member_social' scope\n" \
                           f"Please check your LinkedIn app settings and ensure the app has the correct permissions.\n" \
                           f"API Response: {error_details}"
                else:
                    return f"Error creating post: {str(e)}\nAPI Response: {error_details}"
            except:
                pass
        return f"Error creating post: {str(e)}"


# MCP Tool decorators that call the internal functions
@mcp.tool
def get_profile_info(ctx: Context) -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Returns:
        String containing formatted profile information or error message
    """
    return _get_profile_info(ctx)


@mcp.tool
def create_post(
    ctx: Context,
    commentary: str,
    visibility: str = "PUBLIC",
    feed_distribution: str = "MAIN_FEED",
) -> str:
    """
    Create a post on LinkedIn using the Posts API.

    Args:
        commentary: The text content of the post
        visibility: Visibility of the post (PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER)
        feed_distribution: Feed distribution setting (MAIN_FEED, NONE)

    Returns:
        String containing the post creation result or error message
    """
    return _create_post(ctx, commentary, visibility, feed_distribution)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")