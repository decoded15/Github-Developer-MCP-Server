from mcp.server import MCPServer

from github_mcp.github.client import GitHubClient


mcp = MCPServer("GitHub Developer MCP Server")

github = GitHubClient()


@mcp.tool()
def hello_github_developer(name: str) -> str:
    """Greet a developer using the GitHub MCP Server."""
    return f"Hey {name}! Your GitHub MCP Server is running successfully."


@mcp.tool()
async def get_repository(owner: str, repo: str) -> dict:
    """
    Retrieve information about a public GitHub repository.

    Args:
        owner: GitHub username or organization name.
        repo: Repository name.
    """
    repository = await github.get_repository(owner, repo)

    return {
        "name": repository.get("name"),
        "full_name": repository.get("full_name"),
        "description": repository.get("description"),
        "url": repository.get("html_url"),
        "stars": repository.get("stargazers_count"),
        "forks": repository.get("forks_count"),
        "open_issues": repository.get("open_issues_count"),
        "language": repository.get("language"),
        "default_branch": repository.get("default_branch"),
        "private": repository.get("private"),
    }

@mcp.tool()
async def get_languages(owner: str, repo: str) -> dict:
    """
    Get programming languages used in a GitHub repository.

    Args:
        owner: GitHub username or organization name.
        repo: Repository name.
    """
    return await github.get_languages(owner, repo)

if __name__ == "__main__":
    mcp.run()