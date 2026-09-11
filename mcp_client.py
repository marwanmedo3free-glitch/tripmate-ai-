import os
import sys
import shutil
import traceback
from pathlib import Path

import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq


# ==========================================
# Environment configuration
# ==========================================

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY") or os.getenv("AVIATION_STACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ==========================================
# LLM
# ==========================================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


# ==========================================
# MCP client configuration
# ==========================================

# Resolve full path to uvx on Windows to avoid process launch failures
uvx_executable = shutil.which("uvx") or "uvx"

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            )
        },

        "aviationstack": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                "-m",
                "aviationstack_mcp"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY or ""
            }
        }
    }
)


async def get_all_tools():
    all_tools = []

    for server_name in ("tavily", "aviationstack"):
        try:
            print(f"\nConnecting to {server_name}...")

            tools = await client.get_tools(
                server_name=server_name
            )

            all_tools.extend(tools)

            print(f"\nAvailable tools from {server_name} MCP:\n")

            for tool in tools:
                print(tool.name)

        except Exception as error:
            print(f"\nCould not connect to {server_name} MCP")
            print(f"Error type: {type(error).__name__}")
            print(f"Error: {error}")
            traceback.print_exc()

    return all_tools


# ==========================================
# Tavily MCP tool
# ==========================================

search_tool = None


async def initialize_mcp():
    """
    Initialize only Tavily.
    """
    global search_tool

    if search_tool is not None:
        return

    tools = await client.get_tools(
        server_name="tavily"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    search_tool = tools_by_name.get("tavily_search")

    if search_tool is None:
        available_tools = ", ".join(tools_by_name.keys())
        raise RuntimeError(
            "Tavily MCP connected, but the 'tavily_search' tool was not found. "
            f"Available tools: {available_tools or 'none'}"
        )


async def tavily_mcp_search(query: str):
    await initialize_mcp()

    result = await search_tool.ainvoke({"query": query})
    return result


# ==========================================
# AviationStack MCP tools
# ==========================================

aviation_tools = {}


async def initialize_aviation_tools():
    global aviation_tools

    if aviation_tools:
        return

    tools = await client.get_tools(
        server_name="aviationstack"
    )

    aviation_tools = {
        tool.name: tool
        for tool in tools
    }

    if not aviation_tools:
        raise RuntimeError(
            "AviationStack MCP connected but returned no tools."
        )


async def aviation_mcp_call(tool_name: str, tool_args: dict = None):
    await initialize_aviation_tools()

    tool = aviation_tools.get(tool_name)

    if tool is None:
        available_tools = ", ".join(sorted(aviation_tools.keys()))
        raise ValueError(
            f"AviationStack tool '{tool_name}' was not found. "
            f"Available tools: {available_tools or 'none'}"
        )

    result = await tool.ainvoke(tool_args or {})
    return result


# ==========================================
# Destination extractor
# ==========================================

def extract_destination(query: str):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)
    return response.content.strip()


if __name__ == "__main__":
    import asyncio

    async def main():
        tools = await get_all_tools()
        print(f"\nTotal loaded tools: {len(tools)}")

    asyncio.run(main())