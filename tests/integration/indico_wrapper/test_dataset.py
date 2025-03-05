"""
Test Datasets class methods
"""

import pytest
from indico.types import Dataset

from indico_toolkit.indico_wrapper import Datasets


@pytest.fixture(scope="module")
def dataset_wrapper(indico_client):
    return Datasets(indico_client)


def test_get_dataset(dataset_wrapper, dataset_id):
    dataset = dataset_wrapper.get_dataset(dataset_id)
    assert isinstance(dataset, Dataset)


def test_add_to_dataset(dataset_wrapper, dataset_id, pdf_file):
    dataset = dataset_wrapper.add_files_to_dataset(dataset_id, filepaths=[pdf_file])
    assert isinstance(dataset, Dataset)
    for f in dataset.files:
        assert f.status in ["PROCESSED", "FAILED"]


def test_get_dataset_files(dataset_wrapper, dataset_id):
    files_list = dataset_wrapper.get_dataset_metadata(dataset_id)
    assert isinstance(files_list, list)
    assert len(files_list) > 0


def test_create_delete_dataset(dataset_wrapper, pdf_file):
    dataset = dataset_wrapper.create_dataset(
        filepaths=[pdf_file], dataset_name="Toolkit Integration Tests"
    )
    assert isinstance(dataset, Dataset)
    status = dataset_wrapper.delete_dataset(dataset.id)
    assert status == True
