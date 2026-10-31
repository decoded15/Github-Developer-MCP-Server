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

    async def get_repository_tree(
    self,
    owner: str,
    repo: str,
    max_entries: int = 200,
) -> dict:

        # Find the repository's default branch
        repository = await self.get_repository(owner, repo)
        branch = repository["default_branch"]

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=30.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
            )

            response.raise_for_status()

            data = response.json()
            entries = data.get("tree", [])

            limited_entries = entries[:max_entries]

            return {
                "repository": f"{owner}/{repo}",
                "branch": branch,
                "total_entries": len(entries),
                "returned_entries": len(limited_entries),
                "truncated": data.get("truncated", False)
                or len(entries) > max_entries,
                "tree": [
                    {
                        "path": item["path"],
                        "type": item["type"],
                        "size": item.get("size"),
                        "sha": item["sha"],
                    }
                    for item in limited_entries
                ],
            }
    async def get_file_contents(
    self,
    owner: str,
    repo: str,
    path: str,
) -> dict:

        repository = await self.get_repository(owner, repo)
        branch = repository["default_branch"]

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
            )

            response.raise_for_status()

            data = response.json()

            if data.get("encoding") != "base64":
                raise ValueError("Unsupported file encoding")

            content = base64.b64decode(
                data["content"]
            ).decode("utf-8", errors="replace")

            return {
                "name": data["name"],
                "path": data["path"],
                "content": content,
                "size": data["size"],
                "download_url": data.get("download_url"),
            }
    async def get_dependency_manifests(
    self,
    owner: str,
    repo: str,
) -> dict:

        supported_manifests = {
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "cargo.toml",
            "go.mod",
        }

        repository_tree = await self.get_repository_tree(
            owner,
            repo,
            max_entries=500,
        )

        manifest_paths = [
            item["path"]
            for item in repository_tree["tree"]
            if item["type"] == "blob"
            and item["path"].split("/")[-1].lower()
            in supported_manifests
        ]

        manifests = []

        for path in manifest_paths[:10]:
            try:
                file_data = await self.get_file_contents(
                    owner,
                    repo,
                    path,
                )

                manifests.append(file_data)

            except (httpx.HTTPError, ValueError) as error:
                manifests.append({
                    "path": path,
                    "error": str(error),
                })

        return {
            "repository": f"{owner}/{repo}",
            "manifests_found": len(manifest_paths),
            "manifests_returned": len(manifests),
            "manifests": manifests,
            "tree_truncated": repository_tree["truncated"],
        }