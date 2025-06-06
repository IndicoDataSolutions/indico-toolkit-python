from pathlib import Path

import pytest

from indico_toolkit import results
from indico_toolkit.results import ResultError

data_folder = Path(__file__).parent.parent / "data" / "results"


@pytest.mark.parametrize("result_file", list(data_folder.glob("*.json")))
def test_file_load(result_file: Path) -> None:
    result = results.load(result_file, reader=Path.read_text)
    result.pre_review.to_changes(result)
    assert result.version


@pytest.mark.parametrize("result_file", list(data_folder.glob("*.json")))
async def test_file_load_async(result_file: Path) -> None:
    async def path_read_text_async(path: Path) -> str:
        return path.read_text()

    result = await results.load_async(result_file, reader=path_read_text_async)
    result.pre_review.to_changes(result)
    assert result.version


def test_usupported_version() -> None:
    with pytest.raises(ResultError):
        results.load({"file_version": 1})
