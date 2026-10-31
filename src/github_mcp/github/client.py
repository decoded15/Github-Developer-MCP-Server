import httpx
import base64

from github_mcp.config import GITHUB_TOKEN

class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async def get_repository(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}"
            )

            response.raise_for_status()

            return response.json()
        
    async def get_languages(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/languages"
            )

            response.raise_for_status()

            return response.json()

    async def list_repositories(
        self,
        owner: str,
        per_page: int = 10
    ) -> list[dict]:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/users/{owner}/repos",
                params={
                    "sort": "updated",
                    "per_page": per_page,
                },
            )

            response.raise_for_status()

            return response.json()
    async def get_readme(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/readme"
            )

            response.raise_for_status()

            data = response.json()

            encoded_content = data["content"]

            decoded_content = base64.b64decode(
                encoded_content
            ).decode("utf-8", errors="replace")

            return {
                "name": data["name"],
                "path": data["path"],
                "download_url": data["download_url"],
                "content": decoded_content,
            }