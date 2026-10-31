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

@mcp.tool()
async def list_repositories(
    owner: str,
    per_page: int = 10
) -> list[dict]:
    """
    List recently updated public repositories of a GitHub user.

    Args:
        owner: GitHub username.
        per_page: Maximum number of repositories to return (1-100).
    """

    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")

    repositories = await github.list_repositories(
        owner,
        per_page,
    )

    return [
        {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo["description"],
            "stars": repo["stargazers_count"],
            "language": repo["language"],
            "updated_at": repo["updated_at"],
            "url": repo["html_url"],
        }
        for repo in repositories
    ]

if __name__ == "__main__":
    mcp.run()