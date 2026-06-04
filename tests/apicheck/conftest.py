import pytest

@pytest.fixture
def reset_agent_client(api_manager):
    """agent service服務用，消除舊的client session，後續的api_manager從乾淨狀態重新連線"""
    api_manager.reset_agent_client()
    yield
