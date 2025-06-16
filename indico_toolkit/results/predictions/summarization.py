from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..review import Review
from ..utils import get, has, omit
from .citation import NULL_CITATION, Citation
from .extraction import Extraction

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..task import Task
    from .span import Span


@dataclass
class Summarization(Extraction):
    citations: "list[Citation]"

    @property
    def citation(self) -> Citation:
        """
        Return the first `Citation` the summarization covers else `NULL_CITATION`.

        Post-review, summarizations have no citations.
        """
        return self.citations[0] if self.citations else NULL_CITATION

    @citation.setter
    def citation(self, citation: Citation) -> None:
        """
        Overwrite all citations with the one provided, handling `NULL_CITATION`.

        This is implemented under the assumption that if you're setting a single
        citation, you want it to be the only one. And if you're working in a context
        that's multiple-citation sensetive, you'll set `summarization.citations`
        instead.
        """
        self.citations = [citation] if citation else []

    @property
    def spans(self) -> "tuple[Span, ...]":
        """
        Return the spans covered by `self.citations`.
        """
        return tuple(citation.span for citation in self.citations)

    @property
    def span(self) -> "Span":
        """
        Return the `Span` the first citation covers else `NULL_SPAN`.

        Post-review, summarizations have no citations/spans.
        """
        return self.citation.span

    @span.setter
    def span(self, span: "Span") -> None:
        """
        Overwrite all citations with the first,
        replacing its span with the one provided.

        Using `NULL_SPAN` for a citation is not explicitly handled,
        and should be considered undefined behavior.

        This is implemented under the assumption that if you're setting a single span,
        there's only one citation and you want to update its span. And if you're
        working in a context that's multiple-citation/span sensetive, you'll set
        `summarization.citations` instead.
        """
        self.citation = replace(self.citation, span=span)

    @staticmethod
    def from_dict(
        document: "Document",
        task: "Task",
        review: "Review | None",
        prediction: object,
    ) -> "Summarization":
        """
        Create a `Summarization` from a prediction dictionary.
        """
        return Summarization(
            document=document,
            task=task,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            text=get(prediction, str, "text"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            citations=sorted(
                map(Citation.from_dict, get(prediction, list, "citations"))
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "text",
                "accepted",
                "rejected",
                "citations",
            ),
        )

    def to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "text": self.text,
            "citations": [citation.to_dict() for citation in self.citations],
        }

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
