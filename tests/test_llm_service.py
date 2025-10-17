import pytest
from app.services.llm_service import LLMService
from unittest.mock import Mock


@pytest.fixture
def llm_service():
    return LLMService()


@pytest.mark.asyncio
async def test_generate_app(llm_service, mocker):
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"index.html": "<html></html>"}'))]
    
    mocker.patch.object(
        llm_service.client.chat.completions,
        'create',
        return_value=mock_response
    )
    
    attachments = [{"name": "sample.png", "url": "data:image/png;base64,AAAA"}]
    result = await llm_service.generate_app("Create a simple page", attachments, 1)
    
    assert "index.html" in result
    assert result["index.html"] == "<html></html>"


@pytest.mark.asyncio
async def test_generate_readme(llm_service, mocker):
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="# Test README"))]
    
    mocker.patch.object(
        llm_service.client.chat.completions,
        'create',
        return_value=mock_response
    )
    
    result = await llm_service.generate_readme("test-app", "Test brief", 1)
    
    assert "# Test README" in result