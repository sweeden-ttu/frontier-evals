import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_skip_conditions():
    with patch('swelancer.utils.general.is_linux_machine', return_value=True), \
         patch('swelancer.utils.general.is_docker_running', return_value=True), \
         patch('swelancer.utils.general.is_docker_image', return_value=True):
        yield
