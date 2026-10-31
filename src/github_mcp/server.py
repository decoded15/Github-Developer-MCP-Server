from mcp.server import MCPServer

mcp = MCPServer("GitHub Developer MCP Server")

@mcp.tool()
def hello_github_developer(name: str) -> str:
    """
    Greet a developer using the GitHub MCP Server.
    """
    return f"Hey {name}! Your GitHub MCP Server is running successfully."

if __name__ == "__main__":
    mcp.run()