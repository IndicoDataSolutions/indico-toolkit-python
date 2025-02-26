from pathlib import Path

import pytest


@pytest.fixture
def tests_folder() -> Path:
    return Path(__file__).parent


@pytest.fixture
def snapshot_file(tests_folder: Path) -> Path:
    return tests_folder / "data/snapshots/updated_snapshot.csv"


@pytest.fixture
def old_snapshot_file(tests_folder: Path) -> Path:
    return tests_folder / "data/snapshots/snapshot.csv"
