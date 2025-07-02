"""LinkedIn MCP Server - OAuth-based LinkedIn API integration for MCP"""

from .client import LinkedInOAuthClient, get_client
from .tools import get_profile_info, refresh_token, _get_profile_info, _refresh_token

__version__ = "1.0.0"
__all__ = [
    "LinkedInOAuthClient",
    "get_client",
    "get_profile_info",
    "refresh_token",
    "_get_profile_info",
    "_refresh_token",
]
