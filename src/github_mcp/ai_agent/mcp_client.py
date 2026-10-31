
import asyncio

from mcp import Client, StdioServerParameters


# Configuration for launching our existing MCP server
server_params = StdioServerParameters(
    command="uv",
    args=[
        "run",
        "python",
        "-m",
        "github_mcp.server",
    ],
)


async def main():
    print("Connecting to GitHub Developer MCP Server...")

    async with Client(server_params) as client:
        print("\nConnected successfully!")

        # Discover tools exposed by the server
        result = await client.list_tools()

        print(f"\nDiscovered {len(result.tools)} tools:\n")

        for tool in result.tools:
            print(f"Name: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input schema: {tool.input_schema}")
            print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
