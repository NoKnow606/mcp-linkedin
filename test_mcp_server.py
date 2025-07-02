#!/usr/bin/env python3
"""
Test script to verify MCP server tools are properly exposed.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_linkedin.tools import mcp

async def test_mcp_tools():
    """Test that all MCP tools are properly registered."""
    print("🔍 Testing MCP Server Tool Registration")
    print("=" * 50)
    
    # Get the tools using the async get_tools method
    try:
        tools_list = await mcp.get_tools()
        print(f"📊 Found {len(tools_list)} tools:")
        print("-" * 30)
        
        registered_tools = []
        
        for tool in tools_list:
            tool_name = tool.name if hasattr(tool, 'name') else str(tool)
            print(f"✅ {tool_name}")
            if hasattr(tool, 'description'):
                print(f"   Description: {tool.description}")
            registered_tools.append(tool_name)
        
        expected_tools = [
            "get_profile_info",
            "refresh_token", 
            "create_post"
        ]
        
        print("\n" + "=" * 50)
        print("🔍 Verification Results:")
        print("-" * 30)
        
        missing_tools = set(expected_tools) - set(registered_tools)
        extra_tools = set(registered_tools) - set(expected_tools)
        
        if not missing_tools and not extra_tools:
            print("✅ All expected tools are registered correctly!")
            success = True
        else:
            if missing_tools:
                print(f"❌ Missing tools: {', '.join(missing_tools)}")
            if extra_tools:
                print(f"ℹ️  Extra tools found: {', '.join(extra_tools)}")
            success = len(missing_tools) == 0
        
        print(f"\n📋 Total tools registered: {len(registered_tools)}")
        print(f"📋 Expected tools: {len(expected_tools)}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error getting tools: {e}")
        return False

async def main():
    """Main async function to run the test."""
    success = await test_mcp_tools()
    print(f"\n🎯 Test {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 