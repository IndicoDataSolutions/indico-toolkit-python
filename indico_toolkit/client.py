from typing import Any

from indico import IndicoClient, IndicoConfig
from indico.errors import IndicoAuthenticationFailed, IndicoRequestError

from .errors import ToolkitAuthError
from .retry import retry


@retry(IndicoRequestError, ConnectionError)
def create_client(  # type: ignore[no-any-unimported]
    host: str,
    api_token_path: "str | None" = None,
    api_token_string: "str | None" = None,
    verify_ssl: bool = True,
    **kwargs: Any,
) -> IndicoClient:
    """
    Instantiate your Indico API client.
    Specify either the path to your token or the token string itself.
    """
    config = IndicoConfig(
        host=host,
        api_token_path=api_token_path,
        api_token=api_token_string,
        verify_ssl=verify_ssl,
        **kwargs,
    )
    try:
        return IndicoClient(config)
    except IndicoAuthenticationFailed as e:
        raise ToolkitAuthError(
            f"{e}\nEnsure that you are using your most recently downloaded token with "
            "the correct host URL"
        )
