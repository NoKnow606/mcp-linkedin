import logging
from fastmcp import FastMCP
from src.mcp_linkedin.client import get_client

mcp = FastMCP("mcp-linkedin")
logger = logging.getLogger(__name__)


# Regular functions for testing and direct usage
def _get_profile_info() -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Returns:
        String containing formatted profile information or error message
    """
    try:
        client = get_client()
        profile = client.get_profile()

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
        client = get_client()

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
def get_profile_info() -> str:
    """
    Get the authenticated user's LinkedIn profile information.

    Returns:
        String containing formatted profile information or error message
    """
    logger.info("Getting profile info")
    return _get_profile_info()


@mcp.tool
def create_post(
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
    logger.info("create post")
    return _create_post(commentary, visibility, feed_distribution)


if __name__ == "__main__":
    mcp.run()