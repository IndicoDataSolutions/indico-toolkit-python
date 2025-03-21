import pytest
from indico.types import Submission

from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.ocr import OnDoc
from indico_toolkit.types import WorkflowResult
from indico_toolkit.types.extractions import Extractions


def test_submit_documents_to_workflow(indico_client, pdf_file, workflow_id):
    wflow = Workflow(indico_client)
    sub_ids = wflow.submit_documents_to_workflow(workflow_id, files=[pdf_file])
    assert len(sub_ids) == 1
    assert isinstance(sub_ids[0], int)


@pytest.mark.skip(reason="relies on deprecated v1 result file format")
def test_get_ondoc_ocr_from_etl_url(indico_client, wflow_submission_result):
    wflow = Workflow(indico_client)
    on_doc = wflow.get_ondoc_ocr_from_etl_url(wflow_submission_result.etl_url)
    assert isinstance(on_doc, OnDoc)
    assert on_doc.total_pages == 2


def test_mark_submission_as_retreived(indico_client, function_submission_ids):
    wflow = Workflow(indico_client)
    wflow.mark_submission_as_retreived(submission_id=function_submission_ids[0])


def test_get_complete_submission_objects(
    indico_client, workflow_id, module_submission_ids
):
    wflow = Workflow(indico_client)
    sub_list = wflow.get_complete_submission_objects(workflow_id, module_submission_ids)
    assert isinstance(sub_list, list)


def test_get_submission_object(indico_client, module_submission_ids):
    wflow = Workflow(indico_client)
    sub = wflow.get_submission_object(module_submission_ids[0])
    assert isinstance(sub, Submission)


@pytest.mark.skip(reason="broken on indico-client>=6.1.0")
def test_get_submission_results_from_ids(indico_client, module_submission_ids):
    wflow = Workflow(indico_client)
    result = wflow.get_submission_results_from_ids([module_submission_ids[0]])[0]
    assert isinstance(result, WorkflowResult)
    assert isinstance(result.get_predictions, Extractions)
