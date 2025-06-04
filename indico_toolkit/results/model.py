from dataclasses import dataclass
from enum import Enum

from .utils import get


class ModelGroupType(Enum):
    CLASSIFICATION = "classification"
    DOCUMENT_EXTRACTION = "annotation"
    FORM_EXTRACTION = "form_extraction"
    GENAI_CLASSIFICATION = "genai_classification"
    GENAI_EXTRACTION = "genai_annotation"
    GENAI_SUMMARIZATION = "summarization"
    UNBUNDLING = "classification_unbundling"


@dataclass(frozen=True, order=True)
class ModelGroup:
    id: int
    name: str
    type: ModelGroupType

    @staticmethod
    def from_dict(model_group: object) -> "ModelGroup":
        """
        Create a `ModelGroup` from a model group dictionary.
        """
        return ModelGroup(
            id=get(model_group, int, "id"),
            name=get(model_group, str, "name"),
            type=ModelGroupType(get(model_group, str, "task_type")),
        )
