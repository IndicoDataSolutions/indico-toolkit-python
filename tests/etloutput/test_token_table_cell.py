from dataclasses import replace
from pathlib import Path

import pytest

from indico_toolkit import etloutput
from indico_toolkit.etloutput import (
    NULL_SPAN,
    CellType,
    EtlOutput,
    Span,
    TableCellNotFoundError,
    TokenNotFoundError,
)

data_folder = Path(__file__).parent.parent / "data" / "etloutput"
etl_output_file = data_folder / "4725" / "111924" / "110239" / "etl_output.json"


def read_uri(uri: str | Path) -> bytes:
    uri = str(uri)
    storage_folder_path = uri.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path
    return file_path.read_bytes()


@pytest.fixture(scope="module")
def etl_output() -> EtlOutput:
    return etloutput.load(etl_output_file, reader=read_uri)


@pytest.fixture
def header_span() -> Span:
    return Span(page=1, start=1281, end=1285)


@pytest.fixture
def content_span() -> Span:
    return Span(page=1, start=1343, end=1349)


def test_text_slice(
    etl_output: EtlOutput, header_span: Span, content_span: Span
) -> None:
    assert etl_output.text[header_span.slice] == "COST"
    assert etl_output.text[content_span.slice] == "720.00"


def test_token(etl_output: EtlOutput, header_span: Span, content_span: Span) -> None:
    header_token = etl_output.token_for(header_span)
    content_token = etl_output.token_for(content_span)

    assert header_token.span == header_span
    assert content_token.span == content_span

    assert header_token.text == "COST"
    assert content_token.text == "720.00"


def test_token_not_found(etl_output: EtlOutput, header_span: Span) -> None:
    with pytest.raises(TokenNotFoundError):
        etl_output.token_for(replace(header_span, page=3))


def test_null_span_not_found(etl_output: EtlOutput) -> None:
    with pytest.raises(TokenNotFoundError):
        etl_output.token_for(NULL_SPAN)


def test_table_cell(
    etl_output: EtlOutput, header_span: Span, content_span: Span
) -> None:
    header_token = etl_output.token_for(header_span)
    content_token = etl_output.token_for(content_span)

    header_table, header_cell = etl_output.table_cell_for(header_token)
    content_table, content_cell = etl_output.table_cell_for(content_token)

    assert header_cell.span == header_span
    assert content_cell.span == content_span

    assert header_cell.type == CellType.HEADER
    assert content_cell.type == CellType.CONTENT

    assert header_cell.text == "COST"
    assert content_cell.text == "720.00"


def test_table_cell_not_found(etl_output: EtlOutput) -> None:
    with pytest.raises(TableCellNotFoundError):
        token = etl_output.token_for(Span(page=0, start=0, end=8))
        etl_output.table_cell_for(token)


def test_empty_cell(etl_output: EtlOutput) -> None:
    table = etl_output.tables[2]
    filled_cell = table.rows[1][2]
    empty_cell = table.rows[1][3]

    assert filled_cell.text
    assert not empty_cell.text

    assert filled_cell.span
    assert not empty_cell.span
    assert empty_cell.span == NULL_SPAN
