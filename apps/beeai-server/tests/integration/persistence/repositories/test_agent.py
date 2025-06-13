from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from kink import Container

from fastapi.testclient import TestClient
from beeai_server.configuration import Configuration, FeatureFlagsConfiguration, UIFeatureFlags
from beeai_server.service_layer.deployment_manager import IProviderDeploymentManager

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def beeai_server_sqlalchemy(beeai_server) -> TestClient:
    container = Container()
    container[Configuration] = Configuration(
        feature_flags=FeatureFlagsConfiguration(ui=UIFeatureFlags(user_navigation=False))
    )
    container[IProviderDeploymentManager] = MagicMock()
    with beeai_server(container) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_create_agent(beeai_server_sqlalchemy: TestClient):
    response = beeai_server_sqlalchemy.get("/ping")
    assert response.status_code == 200
