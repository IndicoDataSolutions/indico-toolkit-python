from pathlib import Path

import pytest

from indico_toolkit import create_client, ToolkitAuthError


def test_client_creation(host, token):
    if Path(token).is_file():
        create_client(host, token, None)
    else:
        create_client(host, None, token)


def test_client_fail(host):
    with pytest.raises(ToolkitAuthError):
        create_client(host, api_token_string="not_a_real_token")
