import json
from pathlib import Path

import pytest

from indico_toolkit import etloutput

data_folder = Path(__file__).parent.parent / "data" / "etloutput"


def read_uri(uri: str) -> object:
    storage_folder_path = uri.split("/storage/submission/")[-1]
    file_path = data_folder / storage_folder_path

    if file_path.suffix.casefold() == ".json":
        return json.loads(file_path.read_text())
    else:
        return file_path.read_text()


@pytest.mark.parametrize("etl_output_file", list(data_folder.rglob("etl_output.json")))
def test_file_load(etl_output_file: Path) -> None:
    etl_output = etloutput.load(str(etl_output_file), reader=read_uri)
    page_count = len(etl_output.text_on_page)
    char_count = len(etl_output.text)
    token_count = len(etl_output.tokens)
    table_count = len(etl_output.tables)

    assert page_count == 2
    assert 2090 <= char_count <= 2093
    assert 326 <= token_count <= 331
    assert table_count in (0, 4)
