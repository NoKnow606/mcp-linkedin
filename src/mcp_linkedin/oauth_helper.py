#!/usr/bin/env python3
"""
LinkedIn OAuth Helper Script

This script helps you authenticate with LinkedIn and obtain the necessary tokens
for the MCP LinkedIn tool.

Usage:
    python oauth_helper.py

Requirements:
    - LinkedIn Developer App with proper permissions
    - Client ID and Client Secret from your LinkedIn app
"""

import os
import sys
import webbrowser
import urllib.parse
import requests
from typing import Dict, Any


class LinkedInOAuthHelper:
    """Helper class for LinkedIn OAuth authentication flow."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"

        # Scopes needed for the MCP tools
        self.scopes = [
            "openid",  # For ID token
            "profile",  # For profile access
            "email",  # For email access
            "w_member_social",  # For posting to feed
            "r_liteprofile",  # For profile reading
            "r_emailaddress",  # For email reading
        ]

    def get_authorization_url(self, state: str = "mcp-linkedin") -> str:
        """
        Generate the authorization URL for the user to visit.

        Args:
            state: Random state for CSRF protection

        Returns:
            Authorization URL string
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }

        query_string = urllib.parse.urlencode(params)
        return f"{self.authorization_base_url}?{query_string}"

    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: The authorization code from LinkedIn

        Returns:
            Dictionary containing token information
        """
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(self.token_url, data=data, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Token exchange failed: {response.status_code} - {response.text}"
            )

    def save_tokens_to_env(
        self, tokens: Dict[str, Any], env_file: str = ".env"
    ) -> None:
        """
        Save tokens to environment file.

        Args:
            tokens: Token dictionary from LinkedIn
            env_file: Path to environment file
        """
        # Read existing env file if it exists
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                env_content = f.read()

        # Update or add token variables
        token_lines = [
            f"LINKEDIN_ACCESS_TOKEN={tokens.get('access_token', '')}",
            f"LINKEDIN_REFRESH_TOKEN={tokens.get('refresh_token', '')}",
            f"LINKEDIN_ID_TOKEN={tokens.get('id_token', '')}",
        ]

        # Update existing file or create new one
        lines = env_content.split("\n") if env_content else []

        for token_line in token_lines:
            var_name = token_line.split("=")[0]

            # Find and replace existing line or add new one
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{var_name}="):
                    lines[i] = token_line
                    found = True
                    break

            if not found:
                lines.append(token_line)

        # Write back to file
        with open(env_file, "w") as f:
            f.write("\n".join(lines))

        print(f"✅ Tokens saved to {env_file}")


def main():
    """Main OAuth flow."""
    print("🔗 LinkedIn OAuth Helper for MCP LinkedIn Tool")
    print("=" * 50)

    # Get client credentials
    client_id = input("Enter your LinkedIn Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        sys.exit(1)

    client_secret = input("Enter your LinkedIn Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        sys.exit(1)

    # Initialize OAuth helper
    oauth_helper = LinkedInOAuthHelper(client_id, client_secret)

    # Step 1: Get authorization URL
    print("\n📱 Step 1: Authorization")
    auth_url = oauth_helper.get_authorization_url()
    print(f"Opening authorization URL: {auth_url}")

    # Open browser automatically
    try:
        webbrowser.open(auth_url)
        print("✅ Browser opened automatically")
    except Exception:
        print("⚠️  Please manually open the URL above in your browser")

    print("\n📋 Instructions:")
    print("1. Authorize the application in your browser")
    print("2. You'll be redirected to a page that may show an error (this is normal)")
    print("3. Copy the FULL URL from your browser's address bar")
    print("4. Paste it below")

    # Step 2: Get authorization code
    print("\n🔑 Step 2: Authorization Code")
    redirect_response = input("Paste the full redirect URL here: ").strip()

    if not redirect_response:
        print("❌ Redirect URL is required!")
        sys.exit(1)

    # Parse authorization code from URL
    try:
        parsed_url = urllib.parse.urlparse(redirect_response)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if "error" in query_params:
            print(f"❌ Authorization error: {query_params['error'][0]}")
            if "error_description" in query_params:
                print(f"Description: {query_params['error_description'][0]}")
            sys.exit(1)

        if "code" not in query_params:
            print("❌ No authorization code found in URL!")
            sys.exit(1)

        authorization_code = query_params["code"][0]
        print("✅ Authorization code extracted successfully")

    except Exception as e:
        print(f"❌ Error parsing redirect URL: {e}")
        sys.exit(1)

    # Step 3: Exchange code for tokens
    print("\n🎫 Step 3: Token Exchange")
    try:
        tokens = oauth_helper.exchange_code_for_tokens(authorization_code)
        print("✅ Tokens obtained successfully!")

        # Display token information
        print("\n📄 Token Information:")
        print(f"Access Token: {tokens.get('access_token', 'N/A')[:20]}...")
        print(
            f"Refresh Token: {tokens.get('refresh_token', 'N/A')[:20] if tokens.get('refresh_token') else 'N/A'}..."
        )
        print(
            f"ID Token: {tokens.get('id_token', 'N/A')[:20] if tokens.get('id_token') else 'N/A'}..."
        )
        print(f"Expires In: {tokens.get('expires_in', 'N/A')} seconds")

    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        sys.exit(1)

    # Step 4: Save tokens
    print("\n💾 Step 4: Save Tokens")
    save_to_env = input("Save tokens to .env file? (y/n): ").strip().lower()

    if save_to_env in ["y", "yes"]:
        try:
            # Also save client credentials
            tokens["client_id"] = client_id
            tokens["client_secret"] = client_secret

            oauth_helper.save_tokens_to_env(tokens)

            # Also save client credentials
            env_file = ".env"
            with open(env_file, "a") as f:
                f.write(f"\nLINKEDIN_CLIENT_ID={client_id}")
                f.write(f"\nLINKEDIN_CLIENT_SECRET={client_secret}")

            print("✅ All credentials saved to .env file")

        except Exception as e:
            print(f"❌ Error saving tokens: {e}")
    else:
        print("\n📋 Manual Setup:")
        print("Add these environment variables to your .env file:")
        print(f"LINKEDIN_CLIENT_ID={client_id}")
        print(f"LINKEDIN_CLIENT_SECRET={client_secret}")
        print(f"LINKEDIN_ACCESS_TOKEN={tokens.get('access_token', '')}")
        print(f"LINKEDIN_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
        print(f"LINKEDIN_ID_TOKEN={tokens.get('id_token', '')}")

    print("\n🎉 Setup Complete!")
    print("You can now use the MCP LinkedIn tool with OAuth authentication.")
    print("\n💡 Next Steps:")
    print("1. Test the tool with: python src/mcp_linkedin/client.py")
    print("2. Use the MCP server in your preferred application")


if __name__ == "__main__":
    main()
