import os
import tempfile

import pytest
from indico.types import Dataset

from indico_toolkit.indico_wrapper import Download

pd = pytest.importorskip("pandas")


@pytest.fixture(scope="module")
def downloader(indico_client):
    return Download(indico_client)


def test_get_uploaded_csv_dataframe(downloader: Download, dataset_id: int):
    df = downloader.get_uploaded_csv_dataframe(dataset_id)
    assert isinstance(df, pd.DataFrame)
    assert "question_1620" in df.columns, "Missing column from uploaded CSV"


def test_download_export(downloader: Download, dataset: Dataset):
    df = downloader.get_snapshot_dataframe(dataset.id, dataset.labelsets[0].id)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df["text"][0], str)


@pytest.mark.skip(reason="first file is not guaranteed to be a PDF")
def test_download_pdfs(downloader: Download, dataset: Dataset):
    with tempfile.TemporaryDirectory() as tmpdir:
        num_files = downloader.get_dataset_pdfs(
            dataset.id, dataset.labelsets[0].id, tmpdir, max_files_to_download=1
        )
        num_files_downloaded = len(os.listdir(tmpdir))
        assert num_files == num_files_downloaded
