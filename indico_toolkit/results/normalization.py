import re
from itertools import chain
from typing import TYPE_CHECKING

from .utils import get, has

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any


def normalize_result_dict(result: "Any") -> None:
    """
    Fix inconsistencies observed in result files.
    """
    task_type_by_model_group_id = {
        model_group_id: model_group["task_type"]
        for model_group_id, model_group in chain(
            result["modelgroup_metadata"].items(),
            result.get("component_metadata", {}).items(),
        )
    }
    predictions_with_task_type: "Iterator[tuple[Any, str]]" = (
        (prediction, task_type_by_model_group_id.get(model_group_id, ""))
        for submission_result in get(result, list, "submission_results")
        for review_result in chain(
            get(submission_result, dict, "model_results").values(),
            get(submission_result, dict, "component_results").values(),
        )
        for model_group_id, model_results in review_result.items()
        for prediction in model_results
    )

    for prediction, task_type in predictions_with_task_type:
        # Predictions added in review may lack a `confidence` section.
        if "confidence" not in prediction:
            prediction["confidence"] = {prediction["label"]: 0}

        # Document Extractions added in review may lack spans.
        if (
            task_type in ("annotation", "genai_annotation")
            and "spans" not in prediction
        ):
            prediction["spans"] = []

        # Form Extractions added in review may lack bounding boxes.
        # Set values that will equal `NULL_BOX`.
        if task_type == "form_extraction" and "top" not in prediction:
            prediction["page_num"] = 0
            prediction["top"] = 0
            prediction["left"] = 0
            prediction["right"] = 0
            prediction["bottom"] = 0

        # Prior to 6.11, some Extractions lack a `normalized` section after
        # review.
        if (
            task_type in ("annotation", "form_extraction", "genai_annotation")
            and "normalized" not in prediction
        ):
            prediction["normalized"] = {"formatted": prediction["text"]}

        # Document Extractions that didn't go through a linked labels
        # transformer lack a `groupings` section.
        if (
            task_type in ("annotation", "genai_annotation")
            and "groupings" not in prediction
        ):
            prediction["groupings"] = []

        # Summarizations may lack citations after review.
        if task_type == "summarization" and "citations" not in prediction:
            prediction["citations"] = []

    # Prior to 7.2, result files don't include a `component_metadata` section.
    if not has(result, dict, "component_metadata"):
        result["component_metadata"] = {}

    # Prior to 6.8, result files don't include a `reviews` section.
    if not has(result, dict, "reviews"):
        result["reviews"] = {}

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, dict, "reviews").values():
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""

    # Prior to 7.0, result files don't include an `errored_files` section.
    if not has(result, dict, "errored_files"):
        result["errored_files"] = {}

    # Prior to 7.X, errored files may lack filenames.
    for file in get(result, dict, "errored_files").values():
        if not has(file, str, "input_filename") and has(file, str, "reason"):
            match = re.search(r"file '([^']*)' with id", get(file, str, "reason"))
            file["input_filename"] = match.group(1) if match else ""
