import pytest

from indico_toolkit.etloutput.utils import get, has


@pytest.fixture
def cell() -> "dict[str, object]":
    return {
        "cell_type": "header",
        "columns": [0],
        "rows": [0],
        "doc_offsets": [{"start": 285, "end": 289}],
        "position": {"bottom": 1209, "left": 150, "right": 848, "top": 1107},
        "text": "Item",
    }


def test_get_has(cell: "dict[str, object]") -> None:
    assert has(cell, str, "text")
    assert get(cell, str, "text") == "Item"

    assert has(cell, dict, "position")
    assert has(cell, int, "position", "top")
    assert get(cell, int, "position", "top") == 1107

    assert has(cell, list, "doc_offsets")
    assert has(cell, int, "doc_offsets", 0, "start")
    assert get(cell, int, "doc_offsets", 0, "start") == 285


def test_get_has_not(cell: object) -> None:
    assert not has(cell, str, "missing")
    with pytest.raises(KeyError):
        get(cell, str, "missing")

    assert not has(cell, int, "text")
    with pytest.raises(TypeError):
        get(cell, int, "text")

    assert not has(cell, float, "position", "top", 0)
    with pytest.raises(TypeError):
        get(cell, float, "position", "top", 0)

    assert not has(cell, int, "doc_offsets", "0", "start")
    with pytest.raises(TypeError):
        get(cell, int, "doc_offsets", "0", "start")

    assert not has(cell, int, "doc_offsets", -1, "start")
    with pytest.raises(IndexError):
        get(cell, int, "doc_offsets", -1, "start")

    assert not has(cell, int, "doc_offsets", -1, "start")
    with pytest.raises(IndexError):
        get(cell, int, "doc_offsets", 1, "start")
