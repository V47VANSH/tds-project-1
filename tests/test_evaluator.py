import pytest
from app.services.github_service import GitHubService
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def github_service():
    return GitHubService()


@pytest.mark.asyncio
async def test_create_repository(github_service, mocker):
    mock_repo = Mock()
    mock_repo.html_url = "https://github.com/test/repo"
    
    mocker.patch.object(
        github_service.user,
        'create_repo',
        return_value=mock_repo
    )
    
    # Mock get_repo to raise 404
    mocker.patch.object(
        github_service.user,
        'get_repo',
        side_effect=Exception("404")
    )
    
    result = await github_service.create_repository("test-repo", "Test description")
    
    assert result == "https://github.com/test/repo"


@pytest.mark.asyncio
async def test_enable_github_pages(github_service, mocker):
    mock_repo = Mock()
    
    mocker.patch.object(
        github_service.user,
        'get_repo',
        return_value=mock_repo
    )
    
    result = await github_service.enable_github_pages("test-repo")
    
    assert "github.io" in result