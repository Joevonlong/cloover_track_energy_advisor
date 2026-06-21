"""Unit test conftest — patches Settings so no .env file is required."""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def _patch_settings() -> None:  # type: ignore[return]
    mock = MagicMock()
    mock.cors_origins = ["http://localhost:5173"]
    mock.app_env = "test"
    with patch("app.core.config.get_settings", return_value=mock):
        yield
