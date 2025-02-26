import json
import pytest
from pathlib import Path
import os
from indico_toolkit.pipelines import FileProcessing
import tempfile


def test_get_file_paths_from_dir(tests_folder):
    test_dir = os.path.join(tests_folder, "data/samples/")
    fileproc = FileProcessing()
    fileproc.get_file_paths_from_dir(test_dir, accepted_types=(".pdf", ".json"))
    assert len(fileproc.file_paths) == 4
    assert len(fileproc.invalid_suffix_paths) == 1


def test_from_dir_absent_suffix(tests_folder):
    test_dir = os.path.join(tests_folder, "data/samples/")
    fileproc = FileProcessing()
    with pytest.raises(Exception):
        fileproc.get_file_paths_from_dir(test_dir, accepted_types=".docx")


def test_get_file_paths_from_dir_recursive(tests_folder):
    test_dir = os.path.join(tests_folder, "data/")
    fileproc = FileProcessing()
    fileproc.get_file_paths_from_dir(
        test_dir, accepted_types=(".json",), recursive_search=True
    )
    assert len(fileproc.file_paths) == len(list(Path(test_dir).glob("**/*.json")))
    for fpath in fileproc.file_paths:
        assert fpath.endswith(".json")


def test_move_all_filepaths():
    fileproc = FileProcessing()
    with tempfile.TemporaryDirectory() as temp_dir_one:
        temp_dir_two = tempfile.TemporaryDirectory()
        temp = tempfile.NamedTemporaryFile(dir=temp_dir_one, suffix='.pdf')
        fileproc.move_all_file_paths(temp_dir_one,temp_dir_two.name,('pdf'),True)
        assert os.listdir(temp_dir_two.name) == [Path(temp.name).name]


def test_batch_files(tests_folder):
    test_dir = os.path.join(tests_folder, "data/auto_class/")
    fileproc = FileProcessing()
    fileproc.get_file_paths_from_dir(
        test_dir, accepted_types=(".json", ".pdf", ".csv"), recursive_search=True
    )
    batches = [i for i in fileproc.batch_files(1)]
    assert len(batches) == 2
    assert len(batches[0]) == 1
    assert len(batches[1]) == 1


def test_remove_specified_files(tests_folder):
    test_dir = os.path.join(tests_folder, "data/")
    fileproc = FileProcessing()
    fileproc.get_file_paths_from_dir(
        test_dir, accepted_types=(".json", ".pdf", ".csv"), recursive_search=True
    )
    file_to_remove = fileproc.file_paths[0]
    processed_files = [Path(file_to_remove).name]
    fileproc.remove_files_if_processed(processed_files)
    assert file_to_remove not in fileproc.file_paths


def test_read_json(tests_folder):
    json_path = os.path.join(tests_folder, "data/samples/fin_disc_result.json")
    obj = FileProcessing.read_json(json_path)
    assert isinstance(obj, dict)
    assert "submission_id" in obj
