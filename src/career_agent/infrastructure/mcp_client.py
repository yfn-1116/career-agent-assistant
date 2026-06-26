"""MCP Client — connect to Model Context Protocol servers via stdio.

Enables the Agent to call external MCP servers (GitHub, filesystem, etc.)
by spawning them as subprocesses and communicating via JSON-RPC over stdio.

Usage:
    client = MCPClient("github", "npx", ["-y", "@modelcontextprotocol/server-github"])
    tools = client.list_tools()
    result = client.call_tool("search_repositories", {"query": "career-agent"})
"""

from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPTool:
    """Metadata for an MCP server tool."""
    name: str = ""
    description: str = ""
    input_schema: dict = field(default_factory=dict)
    server_name: str = ""


class MCPClient:
    """Generic MCP client that spawns a server subprocess and talks JSON-RPC.

    Parameters
    ----------
    server_name : str
        Human-readable name for this MCP server.
    command : str
        Executable to launch (e.g. "npx", "python").
    args : list[str]
        Arguments for the command.
    env : dict, optional
        Extra environment variables passed to the subprocess.
    """

    def __init__(
        self,
        server_name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.server_name = server_name
        self._command = command
        self._args = args or []
        self._env = env
        self._process: subprocess.Popen | None = None
        self._tools: list[MCPTool] = []

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        """Launch the MCP server subprocess and initialize."""
        import os

        merged_env = os.environ.copy()
        if self._env:
            merged_env.update(self._env)

        cmd = [self._command] + self._args

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=merged_env,
            text=True,
        )

        # Initialize
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "career-agent", "version": "1.0"},
        })
        self._read_response()

        # Fetch tool list
        tools = self.list_tools()
        self._tools = [
            MCPTool(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
                server_name=self.server_name,
            )
            for t in tools
        ]

    def stop(self) -> None:
        """Terminate the MCP server subprocess."""
        if self._process:
            self._process.terminate()
            self._process = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    # -- MCP protocol --------------------------------------------------------

    def list_tools(self) -> list[dict]:
        """Return the list of tools provided by this MCP server."""
        self._send_request("tools/list", {})
        resp = self._read_response()
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool and return its content as a string."""
        if not self.is_running():
            self.start()

        self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        resp = self._read_response()
        result = resp.get("result", {})
        content = result.get("content", [])
        if isinstance(content, list) and content:
            texts = []
            for item in content:
                if isinstance(item, dict):
                    texts.append(item.get("text", str(item)))
                else:
                    texts.append(str(item))
            return "\n".join(texts)
        return str(content)

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def tool_names(self) -> list[str]:
        return [t.name for t in self._tools]

    # -- JSON-RPC ------------------------------------------------------------

    def _send_request(self, method: str, params: dict) -> None:
        request = {
            "jsonrpc": "2.0",
            "id": uuid.uuid4().hex[:12],
            "method": method,
            "params": params,
        }
        payload = json.dumps(request, ensure_ascii=False) + "\n"
        if self._process and self._process.stdin:
            self._process.stdin.write(payload)
            self._process.stdin.flush()

    def _read_response(self) -> dict:
        if self._process and self._process.stdout:
            line = self._process.stdout.readline()
            if line.strip():
                return json.loads(line)
        return {"error": "no response from MCP server"}


# ---------------------------------------------------------------------------
# Pre-configured MCP servers
# ---------------------------------------------------------------------------


def create_github_mcp(token: str = "") -> MCPClient:
    """Create an MCP client connected to the official GitHub MCP server.

    Requires GITHUB_PERSONAL_ACCESS_TOKEN env var or explicit token.
    """
    import os
    gh_token = token or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not gh_token:
        gh_token = os.environ.get("GITHUB_TOKEN", "")

    return MCPClient(
        server_name="github",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": gh_token} if gh_token else None,
    )
