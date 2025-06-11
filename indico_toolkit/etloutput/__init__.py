from typing import TYPE_CHECKING

from ..results import NULL_BOX, NULL_SPAN, Box, Span
from ..results.utils import get, has
from .cell import Cell, CellType
from .errors import EtlOutputError, TableCellNotFoundError, TokenNotFoundError
from .etloutput import EtlOutput
from .range import Range
from .table import Table
from .token import Token

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import Any

__all__ = (
    "Box",
    "Cell",
    "CellType",
    "EtlOutput",
    "EtlOutputError",
    "load",
    "load_async",
    "NULL_BOX",
    "NULL_SPAN",
    "Range",
    "Span",
    "Table",
    "TableCellNotFoundError",
    "Token",
    "TokenNotFoundError",
)


def load(
    etl_output_uri: str,
    *,
    reader: "Callable[..., Any]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = True,
) -> EtlOutput:
    """
    Load `etl_output_uri` as an `EtlOutput` dataclass. A `reader` function must be
    supplied to read JSON files from disk, storage API, or Indico client.

    Use `text`, `tokens`, and `tables` to specify what to load.

    ```
    result = results.load(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: etloutput.load(document.etl_output_uri, reader=read_uri)
        for document in result.documents
        if not document.failed
    }
    ```
    """
    etl_output = reader(etl_output_uri)
    pages = get(etl_output, list, "pages")

    if text and has(pages, str, 0, "text"):
        text_pages = map(lambda page: reader(get(page, str, "text")), pages)
    else:
        text_pages = ()  # type: ignore[assignment]

    if tokens and has(pages, str, 0, "tokens"):
        token_dict_pages = map(lambda page: reader(get(page, str, "tokens")), pages)
    else:
        token_dict_pages = ()  # type: ignore[assignment]

    if tables and has(pages, str, 0, "tables"):
        table_dict_pages = map(lambda page: reader(get(page, str, "tables")), pages)
    else:
        table_dict_pages = ()  # type: ignore[assignment]

    return EtlOutput.from_pages(text_pages, token_dict_pages, table_dict_pages)


async def load_async(
    etl_output_uri: str,
    *,
    reader: "Callable[..., Awaitable[Any]]",
    text: bool = True,
    tokens: bool = True,
    tables: bool = True,
) -> EtlOutput:
    """
    Load `etl_output_uri` as an `EtlOutput` dataclass. A `reader` coroutine must be
    supplied to read JSON files from disk, storage API, or Indico client.

    Use `text`, `tokens`, and `tables` to specify what to load.

    ```
    result = await results.load_async(submission.result_file, reader=read_uri)
    etl_outputs = {
        document: await etloutput.load_async(document.etl_output_uri, reader=read_uri)
        for document in result.documents
        if not document.failed
    }
    ```
    """
    etl_output = await reader(etl_output_uri)
    pages = get(etl_output, list, "pages")

    if text and has(pages, str, 0, "text"):
        text_pages = [await reader(get(page, str, "text")) for page in pages]
    else:
        text_pages = ()  # type: ignore[assignment]

    if tokens and has(pages, str, 0, "tokens"):
        token_dict_pages = [await reader(get(page, str, "tokens")) for page in pages]
    else:
        token_dict_pages = ()  # type: ignore[assignment]

    if tables and has(pages, str, 0, "tables"):
        table_dict_pages = [await reader(get(page, str, "tables")) for page in pages]
    else:
        table_dict_pages = ()  # type: ignore[assignment]

    return EtlOutput.from_pages(text_pages, token_dict_pages, table_dict_pages)
