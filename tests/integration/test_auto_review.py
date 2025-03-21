import json
import os
from collections import defaultdict

import pytest
from indico.queries import Job

from indico_toolkit.auto_review import AutoReviewer, AutoReviewFunction
from indico_toolkit.auto_review.auto_review_functions import (
    accept_by_all_match_and_confidence,
    accept_by_confidence,
    reject_by_confidence,
    reject_by_max_character_length,
    reject_by_min_character_length,
    remove_by_confidence,
)
from indico_toolkit.indico_wrapper import Workflow

min_max_length = 6
ACCEPTED = "accepted"
REJECTED = "rejected"


@pytest.fixture(scope="session")
def auto_review_preds(tests_folder):
    with open(os.path.join(tests_folder, "data/auto_review/preds.json"), "r") as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="function")
def id_pending_scripted(workflow_id, indico_client, pdf_file):
    """
    Ensure that auto review is turned on and there are two submissions "PENDING_REVIEW"
    """
    wflow = Workflow(indico_client)
    wflow.update_workflow_settings(
        workflow_id, enable_review=True, enable_auto_review=True
    )
    sub_id = wflow.submit_documents_to_workflow(workflow_id, files=[pdf_file])
    wflow.wait_for_submissions_to_process(sub_id)
    return sub_id[0]


@pytest.mark.skip(reason="broken on indico-client>=6.1.0")
def test_submit_submission_review(
    indico_client, id_pending_scripted, wflow_submission_result, model_name
):
    wflow = Workflow(indico_client)
    job = wflow.submit_submission_review(
        id_pending_scripted,
        {model_name: wflow_submission_result.get_predictions.to_list()},
    )
    assert isinstance(job, Job)


@pytest.mark.skip(reason="broken on indico-client>=6.1.0")
def test_submit_auto_review(indico_client, id_pending_scripted, model_name):
    """
    Submit a document to a workflow, auto review the predictions, and retrieve the
    results
    """
    # Submit to workflow and get predictions
    wflow = Workflow(indico_client)
    result = wflow.get_submission_results_from_ids([id_pending_scripted])[0]
    predictions = result.get_predictions.to_list()
    # Review the submission
    functions = [
        AutoReviewFunction(accept_by_confidence, kwargs={"conf_threshold": 0.99}),
        AutoReviewFunction(
            reject_by_min_character_length,
            labels=["Liability Amount", "Date of Appointment"],
            kwargs={"min_length_threshold": 3},
        ),
    ]
    reviewer = AutoReviewer(predictions, functions)
    reviewer.apply_reviews()
    non_rejected_pred_count = len(
        [i for i in reviewer.updated_predictions if "rejected" not in i]
    )
    wflow.submit_submission_review(
        id_pending_scripted, {model_name: reviewer.updated_predictions}
    )
    result = wflow.get_submission_results_from_ids([id_pending_scripted])[0]
    assert result.post_review_predictions.num_predictions == non_rejected_pred_count


def accept_if_match(predictions, labels: list = None, match_text: str = ""):
    for pred in predictions:
        if REJECTED not in pred:
            if labels is not None and pred["label"] not in labels:
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


def test_reviewer(auto_review_preds):
    custom_functions = [
        AutoReviewFunction(
            reject_by_confidence,
            labels=["reject_by_confidence"],
            kwargs={"conf_threshold": 0.7},
        ),
        AutoReviewFunction(
            accept_by_all_match_and_confidence,
            labels=[
                "accept_by_all_match_and_confidence",
                "no_match_accept_by_all_match_and_confidence",
                "low_conf_accept_by_all_match_and_confidence",
            ],
            kwargs={"conf_threshold": 0.9},
        ),
        AutoReviewFunction(
            accept_by_confidence,
            labels=["accept_by_confidence", "reject_by_confidence"],
            kwargs={"conf_threshold": 0.8},
        ),
        AutoReviewFunction(
            remove_by_confidence,
            labels=["remove_by_confidence"],
            kwargs={"conf_threshold": 0.8},
        ),
        AutoReviewFunction(
            reject_by_min_character_length,
            labels=["reject_by_min_character_length"],
            kwargs={"min_length_threshold": 6},
        ),
        AutoReviewFunction(
            reject_by_max_character_length,
            labels=["reject_by_max_character_length"],
            kwargs={"max_length_threshold": 6},
        ),
        AutoReviewFunction(
            accept_if_match,
            labels=["accept_if_match"],
            kwargs={"match_text": "matching text"},
        ),
    ]

    reviewer = AutoReviewer(auto_review_preds, custom_functions)
    reviewer.apply_reviews()
    preds = reviewer.updated_predictions
    pred_map = create_pred_label_map(preds)
    for pred in pred_map["accept_by_all_match_and_confidence"]:
        assert pred[ACCEPTED]
    for pred in pred_map["low_conf_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["no_match_accept_by_all_match_and_confidence"]:
        assert ACCEPTED not in pred
    for pred in pred_map["reject_by_confidence"]:
        if pred["text"] == "low":
            assert pred[REJECTED]
        else:
            assert pred[ACCEPTED]
    for pred in pred_map["reject_by_min_character_length"]:
        if len(pred["text"]) < min_max_length:
            assert pred[REJECTED]
        else:
            assert REJECTED not in pred
    for pred in pred_map["reject_by_max_character_length"]:
        if len(pred["text"]) > min_max_length:
            assert pred[REJECTED]
        else:
            assert REJECTED not in pred
    for pred in pred_map["accept_if_match"]:
        assert pred["accepted"]
    assert "remove_by_confidence" not in pred
