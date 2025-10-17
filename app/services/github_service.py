from github import Github, GithubException
from app.config import settings
import logging
import base64
from typing import Dict

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self):
        self.github = Github(settings.github_token)
        self.user = self.github.get_user()
        self.username = settings.github_username
    
    async def create_repository(self, repo_name: str, description: str) -> str:
        """
        Create a new public repository
        """
        try:
            # Check if repo exists
            try:
                existing_repo = self.user.get_repo(repo_name)
                logger.warning(f"Repository {repo_name} already exists, will update it")
                return existing_repo.html_url
            except GithubException as e:
                if e.status != 404:
                    raise
            
            # Create new repo
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                auto_init=False,
                private=False,
                has_issues=True,
                has_wiki=False,
                has_downloads=True,
            )
            
            logger.info(f"Created repository: {repo.html_url}")
            return repo.html_url
            
        except Exception as e:
            logger.error(f"Error creating repository: {e}")
            raise
    
    async def push_files(self, repo_name: str, files: Dict[str, str], commit_message: str) -> str:
        """
        Push files to repository and return commit SHA
        """
        try:
            repo = self.user.get_repo(repo_name)
            
            # Push each file
            for file_path, content in files.items():
                try:
                    # Check if file exists
                    try:
                        existing_file = repo.get_contents(file_path)
                        # Update existing file
                        repo.update_file(
                            path=file_path,
                            message=commit_message,
                            content=content,
                            sha=existing_file.sha,
                        )
                        logger.info(f"Updated file: {file_path}")
                    except GithubException as e:
                        if e.status == 404:
                            # Create new file
                            repo.create_file(
                                path=file_path,
                                message=commit_message,
                                content=content,
                            )
                            logger.info(f"Created file: {file_path}")
                        else:
                            raise
                except Exception as e:
                    logger.error(f"Error pushing file {file_path}: {e}")
                    raise
            
            # Get latest commit SHA
            commits = repo.get_commits()
            latest_commit = commits[0]
            
            logger.info(f"Pushed files with commit SHA: {latest_commit.sha}")
            return latest_commit.sha
            
        except Exception as e:
            logger.error(f"Error pushing files: {e}")
            raise
    
    async def enable_github_pages(self, repo_name: str) -> str:
        """
        Enable GitHub Pages for the repository
        """
        try:
            repo = self.user.get_repo(repo_name)
            
            # Enable Pages with main branch
            try:
                repo.create_pages_site(source={"branch": "main", "path": "/"})
                logger.info(f"Enabled GitHub Pages for {repo_name}")
            except GithubException as e:
                if "already enabled" in str(e).lower():
                    logger.info(f"GitHub Pages already enabled for {repo_name}")
                else:
                    logger.warning(f"Could not enable Pages: {e}")
            
            # Construct Pages URL
            pages_url = f"https://{self.username}.github.io/{repo_name}/"
            
            return pages_url
            
        except Exception as e:
            logger.error(f"Error enabling GitHub Pages: {e}")
            raise
    
    async def add_mit_license(self, repo_name: str) -> None:
        """
        Add MIT License to repository
        """
        mit_license = """MIT License

Copyright (c) 2025 {username}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""".format(username=self.username)
        
        try:
            repo = self.user.get_repo(repo_name)
            
            try:
                existing_license = repo.get_contents("LICENSE")
                repo.update_file(
                    path="LICENSE",
                    message="Update MIT License",
                    content=mit_license,
                    sha=existing_license.sha,
                )
            except GithubException as e:
                if e.status == 404:
                    repo.create_file(
                        path="LICENSE",
                        message="Add MIT License",
                        content=mit_license,
                    )
                else:
                    raise
            
            logger.info(f"Added MIT License to {repo_name}")
            
        except Exception as e:
            logger.error(f"Error adding license: {e}")
            raise