from copy import copy, deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Self

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

    def __deepcopy__(self, memo: Any) -> "Self":
        """
        Supports `copy.deepcopy(prediction)` without copying immutable objects.
        """
        new_instance = copy(self)
        new_instance.confidences = copy(self.confidences)
        new_instance.extras = deepcopy(self.extras, memo)
        return new_instance

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        raise NotImplementedError()
