import os
import asyncio
import certifi

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load .env
load_dotenv()

# SSL certificates
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# API key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

print("API key loaded:", bool(TAVILY_API_KEY))

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY was not loaded from .env")


client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
        }
    }
)


async def get_all_tools():

    print("\nConnecting to Tavily MCP...\n")

    tools = await client.get_tools()

    print("\nAvailable MCP tools:\n")

    for tool in tools:
        print("-", tool.name)
        
        
tavily_search_tool=None

async def get_tavily_search_tool():
    global tavily_search_tool
    if tavily_search_tool is not None :
        return

    tools =await client.get_tools()
    print("\nAvailable MCP tools:\n")
    for tool in tools:
        print("-", tool.name)
    tavily_search_tool = next((tool for tool in tools if tool.name == "tavily_search"), None)
    
async def tavily_mcp_search(query:str):
    await get_tavily_search_tool()
    result = await tavily_search_tool.ainvoke(
        {
            "query":query
        }  
    )
    return result 
    # print(result)