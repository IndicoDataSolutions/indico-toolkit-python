import os
import json
import pytest
from collections import defaultdict
from indico.queries import Job
from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit.auto_review import ReviewConfiguration, AutoReviewer
from tests.conftest import MODEL_NAME


min_max_length = 6
ACCEPTED = "accepted"
REJECTED = "rejected"


@pytest.fixture(scope="session")
def auto_review_preds(testdir_file_path):
    with open(os.path.join(testdir_file_path, "data/auto_review/preds.json"), "r") as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def auto_review_field_config(testdir_file_path):
    with open(
        os.path.join(testdir_file_path, "data/auto_review/field_config.json"), "r"
    ) as f:
        field_config = json.load(f)
    return field_config


@pytest.fixture(scope="function")
def id_pending_scripted(workflow_id, indico_client, pdf_filepath):
    """
    Ensure that auto review is turned off and there are two submissions "PENDING_REVIEW"
    """
    wflow = Workflow(indico_client)
    wflow.update_workflow_settings(
        workflow_id, enable_review=True, enable_auto_review=True,
    )
    sub_id = wflow.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    wflow.wait_for_submissions_to_process(sub_id)
    return sub_id[0]


def test_submit_submission_review(
    indico_client, id_pending_scripted, wflow_submission_results
):
    wflow = Workflow(indico_client)
    predictions = wflow_submission_results["results"]["document"]["results"][
        MODEL_NAME
    ]["pre_review"]
    job = wflow.submit_submission_review(id_pending_scripted, {MODEL_NAME: predictions})
    assert isinstance(job, Job)


def test_submit_auto_review(indico_client, id_pending_scripted):
    """
    Submit a document to a workflow, auto review the predictions, and retrieve the results
    """
    # Submit to workflow and get predictions
    wflow = Workflow(indico_client)
    result = wflow.get_submission_result_from_id(id_pending_scripted)
    predictions = result["results"]["document"]["results"][MODEL_NAME]["pre_review"]
    # Review the submission
    field_config = [
        {"function": "accept_by_confidence", "kwargs": {"conf_threshold": 0.99}},
        {
            "function": "reject_by_min_character_length",
            "kwargs": {
                "min_length_threshold": 3,
                "labels": ["Liability Amount", "Date of Appointment"],
            },
        },
    ]
    review_config = ReviewConfiguration(field_config)
    reviewer = AutoReviewer(predictions, review_config)
    reviewer.apply_reviews()
    # Submit the changes and retrieve reviewed results
    wflow.submit_submission_review(
        id_pending_scripted, {MODEL_NAME: reviewer.updated_predictions}
    )
    result = wflow.get_submission_result_from_id(id_pending_scripted)
    reviewed_preds = result["results"]["document"]["results"][MODEL_NAME]["final"]
    for pred in reviewed_preds:
        label = pred["label"]
        if (
            label in ["Liability Amount", "Date of Appointment"]
            and len(pred["text"]) < 3
        ):
            assert pred["rejected"] == True
        elif pred["confidence"][label] > 0.99:
            assert pred["accepted"] == True


def accept_if_match(predictions, match_text: str, labels: list = None):
    """Custom function to pass into ReviewConfiguration"""
    for pred in predictions:
        if REJECTED not in pred:
            if labels != None and pred["label"] not in labels:
                continue
            if pred["text"] == match_text:
                pred["accepted"] = True
    return predictions


def create_pred_label_map(predictions):
    """ 
    Create dict with labels keying to list of predictions with that label
    """
    prediction_label_map = defaultdict(list)
    for pred in predictions:
        label = pred["label"]
        prediction_label_map[label].append(pred)
    return prediction_label_map


def test_reviewer(auto_review_field_config, auto_review_preds):
    custom_functions = {"accept_if_match": accept_if_match}
    review_config = ReviewConfiguration(auto_review_field_config, custom_functions)
    reviewer = AutoReviewer(auto_review_preds, review_config)
    reviewer.apply_reviews()
    preds = reviewer.updated_predictions
    pred_map = create_pred_label_map(preds)
    for pred in pred_map["accept_by_all_match_and_confidence"]:
        assert pred[ACCEPTED] == True
    for pred in pred_map["low_conf_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["no_match_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["reject_by_confidence"]:
        if pred["text"] == "low":
            assert pred[REJECTED] == True
        else:
            assert pred[ACCEPTED] == True
    for pred in pred_map["reject_by_min_character_length"]:
        if len(pred["text"]) < min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred
    for pred in pred_map["reject_by_max_character_length"]:
        if len(pred["text"]) > min_max_length:
            assert pred[REJECTED] == True
        else:
            assert REJECTED not in pred
    for pred in pred_map["accept_if_match"]:
        assert pred["accepted"] == True
    assert "remove_by_confidence" not in pred
