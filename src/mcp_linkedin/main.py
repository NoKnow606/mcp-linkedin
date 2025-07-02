"""Main entry point for LinkedIn MCP Server"""

import sys
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from .tools import mcp
except ImportError:
    from mcp_linkedin.tools import mcp


def run_server():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    run_server()
