from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..review import Review
from ..utils import get, omit
from .prediction import Prediction
from .span import Span

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..model import ModelGroup


@dataclass
class Unbundling(Prediction):
    spans: "list[Span]"

    @property
    def pages(self) -> "tuple[int, ...]":
        """
        Return the pages covered by `self.spans`.
        """
        return tuple(span.page for span in self.spans)

    @staticmethod
    def from_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "Unbundling":
        """
        Create an `Unbundling` from a prediction dictionary.
        """
        return Unbundling(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            spans=sorted(map(Span.from_dict, get(prediction, list, "spans"))),
            extras=omit(prediction, "confidence", "label", "spans"),
        )

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        return {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "spans": [span.to_dict() for span in self.spans],
        }
