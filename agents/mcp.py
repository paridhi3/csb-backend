# mcp.py

import importlib
import os
from dotenv import load_dotenv

load_dotenv()

class MCPToolServer:
    """Base class for all MCP Tool Servers."""
    def __init__(self, name):
        self.name = name

    async def run(self, *args, **kwargs):
        raise NotImplementedError


class MCPClient:
    """Main MCP Client that loads and manages tool servers."""
    def __init__(self, servers):
        self.servers = []
        for srv in servers:
            try:
                module = importlib.import_module(srv["module"])
                cls = getattr(module, srv["class"])
                instance = cls()
                self.servers.append(instance)
                print(f"✅ Loaded MCP Tool Server: {srv['class']}")
            except Exception as e:
                print(f"❌ Failed to load {srv['class']}: {e}")

    async def run_all(self, *args, **kwargs):
        results = {}
        for server in self.servers:
            results[server.name] = await server.run(*args, **kwargs)
        return results


def get_llm_config():
    """Returns the LLM API configuration for OpenAI or Azure OpenAI."""
    provider = os.getenv("OPENAI_PROVIDER", "openai").lower()

    if provider == "azure":
        return {
            "type": "azure",
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        }
    else:
        return {
            "type": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        }
