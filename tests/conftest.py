import os
import pytest

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def testdir_file_path():
    return FILE_PATH


@pytest.fixture(scope="session")
def snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/updated_snapshot.csv")


@pytest.fixture(scope="session")
def old_snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/snapshot.csv")
