from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..document import Document
    from ..review import Review
    from ..task import Task


@dataclass
class Prediction:
    document: "Document"
    task: "Task"
    review: "Review | None"

    label: str
    confidences: "dict[str, float]"
    extras: "dict[str, Any]"

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @confidence.setter
    def confidence(self, value: float) -> None:
        self.confidences[self.label] = value

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        raise NotImplementedError()
