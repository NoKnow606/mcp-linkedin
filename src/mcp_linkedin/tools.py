import logging
from fastmcp import FastMCP
from .client import get_client

mcp = FastMCP("mcp-linkedin")
logger = logging.getLogger(__name__)


# Regular functions for testing and direct usage
def _get_profile_info(
    fields: str = "id,localizedFirstName,localizedLastName,localizedHeadline",
) -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Args:
        fields: Comma-separated list of profile fields to retrieve

    Returns:
        String containing formatted profile information or error message
    """
    try:
        client = get_client()
        profile = client.get_profile(fields=fields)

        result = "LinkedIn Profile Information:\n"
        for key, value in profile.items():
            result += f"{key}: {value}\n"

        return result

    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return f"Error retrieving profile: {str(e)}"


def _refresh_token() -> str:
    """
    Manually refresh the LinkedIn access token using the refresh token.

    Returns:
        String indicating success or failure of token refresh
    """
    try:
        client = get_client()
        success = client.refresh_access_token()

        if success:
            return "Access token refreshed successfully."
        else:
            return "Failed to refresh access token. Check your refresh token and client credentials."

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return f"Error refreshing token: {str(e)}"


def _create_post(
    author: str,
    commentary: str,
    visibility: str = "PUBLIC",
    feed_distribution: str = "MAIN_FEED",
) -> str:
    """
    Create a post on LinkedIn using the Posts API.

    Args:
        author: URN of the author (person or organization)
        commentary: The text content of the post
        visibility: Visibility of the post (PUBLIC, CONNECTIONS, LOGGED_IN)
        feed_distribution: Feed distribution setting (MAIN_FEED, NONE)

    Returns:
        String containing the post creation result or error message
    """
    try:
        client = get_client()

        # Create the post payload according to LinkedIn Posts API v2 spec
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
            "isReshareDisabledByAuthor": False,
        }

        # Make the API call to create the post
        response = client._make_request(
            "POST",
            "/posts",  # Using the new Posts API endpoint
            json=post_data,
        )

        response.raise_for_status()

        # Get the post ID from the response header
        post_id = response.headers.get("x-restli-id", "Unknown")

        return f"Post created successfully! Post ID: {post_id}"

    except Exception as e:
        logger.error(f"Error creating post: {e}")
        # If it's an HTTP error, try to get more details
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.text
                logger.error(f"API Error Response: {error_details}")
                return f"Error creating post: {str(e)}\nAPI Response: {error_details}"
            except:
                pass
        return f"Error creating post: {str(e)}"


# MCP Tool decorators that call the internal functions
@mcp.tool()
def get_profile_info(
    fields: str = "id,localizedFirstName,localizedLastName,localizedHeadline",
) -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Args:
        fields: Comma-separated list of profile fields to retrieve

    Returns:
        String containing formatted profile information or error message
    """
    return _get_profile_info(fields)


@mcp.tool()
def refresh_token(random_string: str = "") -> str:
    """
    Manually refresh the LinkedIn access token using the refresh token.

    Returns:
        String indicating success or failure of token refresh
    """
    return _refresh_token()


@mcp.tool()
def create_post(
    author: str,
    commentary: str,
    visibility: str = "PUBLIC",
    feed_distribution: str = "MAIN_FEED",
) -> str:
    """
    Create a post on LinkedIn using the Posts API.

    Args:
        author: URN of the author (person or organization) - e.g., "urn:li:person:123" or "urn:li:organization:456"
        commentary: The text content of the post
        visibility: Visibility of the post (PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER)
        feed_distribution: Feed distribution setting (MAIN_FEED, NONE)

    Returns:
        String containing the post creation result or error message
    """
    return _create_post(author, commentary, visibility, feed_distribution)
