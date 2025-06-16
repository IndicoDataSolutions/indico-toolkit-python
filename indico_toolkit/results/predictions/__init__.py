from typing import TYPE_CHECKING

from ..errors import ResultError
from ..normalization import normalize_prediction_dict
from ..task import TaskType
from .box import NULL_BOX, Box
from .citation import NULL_CITATION, Citation
from .classification import Classification
from .documentextraction import DocumentExtraction
from .extraction import Extraction
from .formextraction import FormExtraction, FormExtractionType
from .group import Group
from .prediction import Prediction
from .span import NULL_SPAN, Span
from .summarization import Summarization
from .unbundling import Unbundling

if TYPE_CHECKING:
    from ..document import Document
    from ..review import Review
    from ..task import Task

__all__ = (
    "Box",
    "Citation",
    "Classification",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "NULL_BOX",
    "NULL_CITATION",
    "NULL_SPAN",
    "Prediction",
    "Span",
    "Summarization",
    "Unbundling",
)


def from_dict(
    document: "Document",
    task: "Task",
    review: "Review | None",
    prediction: object,
) -> "Prediction":
    """
    Create a `Prediction` subclass from a prediction dictionary.
    """
    normalize_prediction_dict(task.type, prediction)

    if task.type in (TaskType.CLASSIFICATION, TaskType.GENAI_CLASSIFICATION):
        return Classification.from_dict(document, task, review, prediction)
    elif task.type in (TaskType.DOCUMENT_EXTRACTION, TaskType.GENAI_EXTRACTION):
        return DocumentExtraction.from_dict(document, task, review, prediction)
    elif task.type == TaskType.FORM_EXTRACTION:
        return FormExtraction.from_dict(document, task, review, prediction)
    elif task.type == TaskType.GENAI_SUMMARIZATION:
        return Summarization.from_dict(document, task, review, prediction)
    elif task.type == TaskType.UNBUNDLING:
        return Unbundling.from_dict(document, task, review, prediction)
    else:
        raise ResultError(f"unsupported task type {task.type!r}")
