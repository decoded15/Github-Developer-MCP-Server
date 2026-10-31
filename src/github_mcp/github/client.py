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

    async def get_commits(
    self,
    owner: str,
    repo: str,
    per_page: int = 10,
) -> list[dict]:

        repository = await self.get_repository(owner, repo)
        branch = repository["default_branch"]

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/commits",
                params={
                    "sha": branch,
                    "per_page": per_page,
                },
            )

            response.raise_for_status()

            data = response.json()

            return [
                {
                    "sha": item["sha"],
                    "message": item["commit"]["message"],
                    "author": (
                        item["commit"]["author"]["name"]
                        if item["commit"].get("author")
                        else None
                    ),
                    "date": (
                        item["commit"]["author"]["date"]
                        if item["commit"].get("author")
                        else None
                    ),
                    "url": item["html_url"],
                }
                for item in data
            ]

    async def get_commit_details(
    self,
    owner: str,
    repo: str,
    commit_sha: str,
) -> dict:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=20.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/commits/{commit_sha}"
            )

            response.raise_for_status()

            data = response.json()

            files = data.get("files", [])

            return {
                "repository": f"{owner}/{repo}",
                "sha": data["sha"],
                "message": data["commit"]["message"],
                "author": (
                    data["commit"]["author"]["name"]
                    if data["commit"].get("author")
                    else None
                ),
                "date": (
                    data["commit"]["author"]["date"]
                    if data["commit"].get("author")
                    else None
                ),
                "statistics": data.get("stats", {}),
                "files_changed": len(files),
                "files": [
                    {
                        "filename": item["filename"],
                        "status": item["status"],
                        "additions": item["additions"],
                        "deletions": item["deletions"],
                        "changes": item["changes"],
                        "patch": item.get("patch"),
                    }
                    for item in files[:30]
                ],
            }
    async def list_issues(
    self,
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 10,
) -> list[dict]:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/issues",
                params={
                    "state": state,
                    "per_page": per_page,
                },
            )

            response.raise_for_status()

            data = response.json()

            return [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "author": issue["user"]["login"],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "url": issue["html_url"],
                    "labels": [
                        label["name"]
                        for label in issue["labels"]
                    ],
                }
                for issue in data
                if "pull_request" not in issue
            ]

    async def get_issue(
    self,
    owner: str,
    repo: str,
    issue_number: int,
) -> dict:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/issues/{issue_number}"
            )

            response.raise_for_status()

            issue = response.json()

            return {
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
                "state": issue["state"],
                "author": issue["user"]["login"],
                "assignees": [
                    user["login"]
                    for user in issue["assignees"]
                ],
                "labels": [
                    label["name"]
                    for label in issue["labels"]
                ],
                "comments_count": issue["comments"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "url": issue["html_url"],
            }

    async def list_pull_requests(
    self,
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 10,
) -> list[dict]:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=15.0,
        ) as client:

            response = await client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={
                    "state": state,
                    "per_page": per_page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )

            response.raise_for_status()

            data = response.json()

            return [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["user"]["login"],
                    "state": pr["state"],
                    "source_branch": pr["head"]["ref"],
                    "target_branch": pr["base"]["ref"],
                    "draft": pr["draft"],
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "url": pr["html_url"],
                }
                for pr in data
            ]

    async def get_pull_request(
    self,
    owner: str,
    repo: str,
    pull_number: int,
) -> dict:

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=20.0,
        ) as client:

            # Fetch PR information
            response = await client.get(
                f"/repos/{owner}/{repo}/pulls/{pull_number}"
            )

            response.raise_for_status()

            pr = response.json()

            # Fetch changed files
            files_response = await client.get(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
                params={"per_page": 30},
            )

            files_response.raise_for_status()

            files = files_response.json()

            return {
                "number": pr["number"],
                "title": pr["title"],
                "body": pr["body"],
                "author": pr["user"]["login"],
                "state": pr["state"],
                "draft": pr["draft"],
                "merged": pr["merged"],
                "source_branch": pr["head"]["ref"],
                "target_branch": pr["base"]["ref"],
                "additions": pr["additions"],
                "deletions": pr["deletions"],
                "changed_files_count": pr["changed_files"],
                "mergeable": pr["mergeable"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "url": pr["html_url"],
                "files": [
                    {
                        "filename": item["filename"],
                        "status": item["status"],
                        "additions": item["additions"],
                        "deletions": item["deletions"],
                        "changes": item["changes"],
                        "patch": item.get("patch"),
                    }
                    for item in files
                ],
            }


    async def build_repository_overview(
        self,
        owner: str,
        repo: str,
        max_tree_entries: int = 150,
    ) -> dict:
        """Collect compact repository intelligence efficiently."""

        import asyncio

        import base64

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=25.0,
        ) as client:

            # ------------------------------------------
            # 1. Fetch metadata ONCE
            # ------------------------------------------

            response = await client.get(
                f"/repos/{owner}/{repo}"
            )
            response.raise_for_status()

            raw_metadata = response.json()

            branch = raw_metadata["default_branch"]

            metadata = {
                "name": raw_metadata.get("name"),
                "full_name": raw_metadata.get("full_name"),
                "description": raw_metadata.get("description"),
                "url": raw_metadata.get("html_url"),
                "default_branch": branch,
                "primary_language": raw_metadata.get("language"),
                "stars": raw_metadata.get("stargazers_count"),
                "forks": raw_metadata.get("forks_count"),
                "open_issues": raw_metadata.get("open_issues_count"),
                "created_at": raw_metadata.get("created_at"),
                "updated_at": raw_metadata.get("updated_at"),
                "pushed_at": raw_metadata.get("pushed_at"),
            }

            # ------------------------------------------
            # 2. Safe request helper
            # ------------------------------------------

            async def fetch_json(endpoint, params=None):
                try:
                    response = await client.get(
                        endpoint,
                        params=params,
                    )
                    response.raise_for_status()

                    return {
                        "status": "available",
                        "data": response.json(),
                    }

                except Exception as error:
                    return {
                        "status": "unavailable",
                        "error": str(error),
                    }

            # ------------------------------------------
            # 3. Fetch independent evidence concurrently
            # ------------------------------------------

            languages_result, readme_result, tree_result, commits_result = (
                await asyncio.gather(
                    fetch_json(
                        f"/repos/{owner}/{repo}/languages"
                    ),
                    fetch_json(
                        f"/repos/{owner}/{repo}/readme"
                    ),
                    fetch_json(
                        f"/repos/{owner}/{repo}/git/trees/{branch}",
                        params={"recursive": "1"},
                    ),
                    fetch_json(
                        f"/repos/{owner}/{repo}/commits",
                        params={
                            "sha": branch,
                            "per_page": 5,
                        },
                    ),
                )
            )

            # ------------------------------------------
            # 4. Process README
            # ------------------------------------------

            if readme_result["status"] == "available":
                try:
                    readme_data = readme_result["data"]

                    readme_content = base64.b64decode(
                        readme_data["content"]
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )

                    readme = {
                        "status": "available",
                        "path": readme_data.get("path"),
                        "content": readme_content[:10000],
                        "truncated": len(readme_content) > 10000,
                    }

                except Exception as error:
                    readme = {
                        "status": "unavailable",
                        "error": str(error),
                    }
            else:
                readme = readme_result

            # ------------------------------------------
            # 5. Process languages
            # ------------------------------------------

            languages = languages_result

            # ------------------------------------------
            # 6. Process tree ONCE
            # ------------------------------------------

            tree = []
            manifest_paths = []
            tree_truncated = False
            total_entries = 0

            supported_manifests = {
                "requirements.txt",
                "pyproject.toml",
                "package.json",
                "cargo.toml",
                "go.mod",
            }

            if tree_result["status"] == "available":

                tree_data = tree_result["data"]

                raw_tree = tree_data.get("tree", [])

                total_entries = len(raw_tree)

                tree_truncated = (
                    tree_data.get("truncated", False)
                    or total_entries > max_tree_entries
                )

                selected_entries = raw_tree[:max_tree_entries]

                tree = [
                    {
                        "path": item["path"],
                        "type": item["type"],
                    }
                    for item in selected_entries
                ]

                manifest_paths = [
                    item["path"]
                    for item in raw_tree
                    if item["type"] == "blob"
                    and item["path"].split("/")[-1].lower()
                    in supported_manifests
                ][:5]

                tree_result = {
                    "status": "available",
                    "data": {
                        "branch": branch,
                        "total_entries": total_entries,
                        "returned_entries": len(tree),
                        "truncated": tree_truncated,
                        "tree": tree,
                    },
                }

            # ------------------------------------------
            # 7. Fetch dependency manifests concurrently
            #    Reuse the existing tree and branch.
            # ------------------------------------------

            async def fetch_manifest(path):
                try:
                    response = await client.get(
                        f"/repos/{owner}/{repo}/contents/{path}",
                        params={"ref": branch},
                    )
                    response.raise_for_status()

                    file_data = response.json()

                    content = base64.b64decode(
                        file_data["content"]
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )

                    return {
                        "path": path,
                        "content": content[:5000],
                        "truncated": len(content) > 5000,
                    }

                except Exception as error:
                    return {
                        "path": path,
                        "error": str(error),
                    }

            manifests = await asyncio.gather(
                *[
                    fetch_manifest(path)
                    for path in manifest_paths
                ]
            )

            dependencies = {
                "status": "available",
                "manifests_found": len(manifest_paths),
                "manifests_returned": len(manifests),
                "manifests": manifests,
                "tree_truncated": tree_truncated,
            }

            # ------------------------------------------
            # 8. Process recent commits
            # ------------------------------------------

            if commits_result["status"] == "available":

                commits = [
                    {
                        "sha": item.get("sha", "")[:10],
                        "message": item.get(
                            "commit", {}
                        ).get("message", "")[:300],
                        "author": (
                            item.get("commit", {})
                            .get("author", {})
                            or {}
                        ).get("name"),
                        "date": (
                            item.get("commit", {})
                            .get("author", {})
                            or {}
                        ).get("date"),
                        "url": item.get("html_url"),
                    }
                    for item in commits_result["data"]
                ]

                commits_result = {
                    "status": "available",
                    "data": commits,
                }

            # ------------------------------------------
            # 9. Return compact evidence
            # ------------------------------------------

            return {
                "repository": f"{owner}/{repo}",
                "metadata": metadata,
                "languages": languages,
                "readme": readme,
                "directory_tree": tree_result,
                "dependencies": dependencies,
                "recent_commits": commits_result,
            }
