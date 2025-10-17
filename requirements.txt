import pytest
from app.services.github_service import GitHubService
from app.config import settings
import time
import asyncio

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def github_service():
    """Real GitHub service for integration testing"""
    return GitHubService()


@pytest.mark.asyncio
async def test_create_repository_integration(github_service):
    """
    Test actual repository creation on GitHub
    WARNING: This will create a real repository!
    """
    repo_name = f"test-repo-{int(time.time())}"  # Unique name
    description = "Integration test repository - safe to delete"
    
    try:
        # Create repository
        repo_url = await github_service.create_repository(repo_name, description)
        
        # Verify URL format
        assert repo_url.startswith("https://github.com/")
        assert repo_name in repo_url
        
        # Wait a moment for GitHub to process
        await asyncio.sleep(2)
        
        # Verify we can access the repo (idempotency test)
        repo_url_2 = await github_service.create_repository(repo_name, description)
        assert repo_url == repo_url_2
        
        print(f"✅ Created repository: {repo_url}")
        
    except Exception as e:
        pytest.fail(f"Repository creation failed: {e}")


@pytest.mark.asyncio
async def test_push_files_integration(github_service):
    """
    Test pushing files to a real repository
    """
    repo_name = f"test-files-{int(time.time())}"
    
    try:
        # Create repo
        await github_service.create_repository(repo_name, "Test files repo")
        await asyncio.sleep(2)
        
        # Push files
        files = {
            "index.html": "<html><body><h1>Test</h1></body></html>",
            "README.md": "# Test Repository\n\nThis is a test.",
            "script.js": "console.log('Hello World');"
        }
        
        commit_sha = await github_service.push_files(
            repo_name, 
            files, 
            "Initial commit with test files"
        )
        
        # Verify commit SHA format
        assert commit_sha is not None
        assert len(commit_sha) == 40  # Git SHA-1 is 40 characters
        
        print(f"✅ Pushed files with commit: {commit_sha}")
        
        # Test updating files
        files["index.html"] = "<html><body><h1>Updated</h1></body></html>"
        commit_sha_2 = await github_service.push_files(
            repo_name,
            files,
            "Update files"
        )
        
        assert commit_sha != commit_sha_2
        print(f"✅ Updated files with commit: {commit_sha_2}")
        
    except Exception as e:
        pytest.fail(f"File push failed: {e}")


@pytest.mark.asyncio
async def test_enable_pages_integration(github_service):
    """
    Test enabling GitHub Pages
    """
    repo_name = f"test-pages-{int(time.time())}"
    
    try:
        # Create repo and push an index.html
        await github_service.create_repository(repo_name, "Test pages repo")
        await asyncio.sleep(2)
        
        files = {"index.html": "<html><body><h1>Hello Pages</h1></body></html>"}
        await github_service.push_files(repo_name, files, "Add index.html")
        await asyncio.sleep(2)
        
        # Enable pages
        pages_url = await github_service.enable_github_pages(repo_name)
        
        # Verify URL format
        assert pages_url.startswith(f"https://{settings.github_username}.github.io/")
        assert repo_name in pages_url
        
        print(f"✅ Enabled Pages: {pages_url}")
        print("⚠️ Note: Pages may take a few minutes to be fully deployed")
        
    except Exception as e:
        pytest.fail(f"Pages enablement failed: {e}")


@pytest.mark.asyncio
async def test_add_license_integration(github_service):
    """
    Test adding MIT License
    """
    repo_name = f"test-license-{int(time.time())}"
    
    try:
        await github_service.create_repository(repo_name, "Test license repo")
        await asyncio.sleep(2)
        
        # Add license
        await github_service.add_mit_license(repo_name)
        
        print(f"✅ Added MIT License to {repo_name}")
        
        # Test idempotency (should not fail if run twice)
        await github_service.add_mit_license(repo_name)
        print(f"✅ Updated MIT License (idempotent)")
        
    except Exception as e:
        pytest.fail(f"License addition failed: {e}")


@pytest.mark.asyncio
async def test_full_workflow_integration(github_service):
    """
    Test complete workflow: create repo, push files, add license, enable pages
    """
    repo_name = f"test-workflow-{int(time.time())}"
    
    try:
        # 1. Create repository
        repo_url = await github_service.create_repository(
            repo_name, 
            "Full workflow integration test"
        )
        print(f"1. ✅ Created repo: {repo_url}")
        await asyncio.sleep(2)
        
        # 2. Add license
        await github_service.add_mit_license(repo_name)
        print(f"2. ✅ Added MIT License")
        await asyncio.sleep(1)
        
        # 3. Push files
        files = {
            "index.html": "<!DOCTYPE html><html><body><h1>Integration Test</h1></body></html>",
            "README.md": f"# {repo_name}\n\nIntegration test repository",
            "styles.css": "body { font-family: Arial; }"
        }
        commit_sha = await github_service.push_files(
            repo_name,
            files,
            "Add application files"
        )
        print(f"3. ✅ Pushed files: {commit_sha}")
        await asyncio.sleep(2)
        
        # 4. Enable GitHub Pages
        pages_url = await github_service.enable_github_pages(repo_name)
        print(f"4. ✅ Enabled Pages: {pages_url}")
        
        # Summary
        print(f"\n📊 Integration Test Summary:")
        print(f"   Repository: {repo_url}")
        print(f"   Latest Commit: {commit_sha}")
        print(f"   Pages URL: {pages_url}")
        print(f"   ⚠️ Pages deployment may take 1-2 minutes")
        
    except Exception as e:
        pytest.fail(f"Full workflow failed: {e}")