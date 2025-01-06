from collections import defaultdict
from operator import attrgetter
from typing import TYPE_CHECKING, List, TypeVar, overload

from .model import TaskType
from .predictions import (
    Classification,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    Prediction,
    Unbundling,
)
from .review import Review, ReviewType
from .utilities import nfilter

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Container, Iterable
    from typing import Any, SupportsIndex

    from typing_extensions import Self

    from .document import Document
    from .model import ModelGroup
    from .result import Result

PredictionType = TypeVar("PredictionType", bound=Prediction)
OfType = TypeVar("OfType", bound=Prediction)
KeyType = TypeVar("KeyType")

# Non-None sentinel value to support `PredictionList.where(review=None)`.
ReviewUnspecified = Review(
    id=None, reviewer_id=None, notes=None, rejected=None, type=None  # type: ignore[arg-type]
)


class PredictionList(List[PredictionType]):
    @property
    def classifications(self) -> "PredictionList[Classification]":
        return self.oftype(Classification)

    @property
    def document_extractions(self) -> "PredictionList[DocumentExtraction]":
        return self.oftype(DocumentExtraction)

    @property
    def extractions(self) -> "PredictionList[Extraction]":
        return self.oftype(Extraction)

    @property
    def form_extractions(self) -> "PredictionList[FormExtraction]":
        return self.oftype(FormExtraction)

    @property
    def unbundlings(self) -> "PredictionList[Unbundling]":
        return self.oftype(Unbundling)

    @overload
    def __getitem__(self, index: "SupportsIndex", /) -> PredictionType: ...
    @overload
    def __getitem__(self, index: slice, /) -> "PredictionList[PredictionType]": ...
    def __getitem__(
        self, index: "SupportsIndex | slice"
    ) -> "PredictionType | PredictionList[PredictionType]":
        if isinstance(index, slice):
            return type(self)(super().__getitem__(index))
        else:
            return super().__getitem__(index)

    def apply(self, function: "Callable[[PredictionType], None]") -> "Self":
        """
        Apply `function` to all predictions.
        """
        for prediction in self:
            function(prediction)

        return self

    def groupby(
        self, key: "Callable[[PredictionType], KeyType]"
    ) -> "dict[KeyType, Self]":
        """
        Group predictions into a dictionary using `key` to derive each prediction's key.
        E.g. `key=attrgetter("label")` or `key=attrgetter("model")`.

        If a derived key is an unhashable mutable collection (like set),
        it's automatically converted to its hashable immutable variant (like frozenset).
        This makes it easy to group by linked labels or unbundling pages.
        """
        grouped = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            derived_key = key(prediction)

            if isinstance(derived_key, list):
                derived_key = tuple(derived_key)  # type: ignore[assignment]
            elif isinstance(derived_key, set):
                derived_key = frozenset(derived_key)  # type: ignore[assignment]

            grouped[derived_key].append(prediction)

        return grouped

    def groupbyiter(
        self, keys: "Callable[[PredictionType], Iterable[KeyType]]"
    ) -> "dict[KeyType, Self]":
        """
        Group predictions into a dictionary using `key` to derive an iterable of keys.
        E.g. `key=attrgetter("groups")` or `key=attrgetter("pages")`.

        Each prediction is associated with every key in the iterable individually.
        If the iterable is empty, the prediction is not included in any group.
        """
        grouped = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            for derived_key in keys(prediction):
                grouped[derived_key].append(prediction)

        return grouped

    def oftype(self, type: "type[OfType]") -> "PredictionList[OfType]":
        """
        Return a new prediction list containing predictions of type `type`.
        """
        return self.where(lambda prediction: isinstance(prediction, type))  # type: ignore[return-value]

    def orderby(
        self,
        key: "Callable[[PredictionType], Any]",
        *,
        reverse: bool = False,
    ) -> "Self":
        """
        Return a new prediction list with predictions sorted by `key`.
        """
        return type(self)(sorted(self, key=key, reverse=reverse))

    def where(
        self,
        predicate: "Callable[[PredictionType], bool] | None" = None,
        *,
        document: "Document | None" = None,
        model: "ModelGroup | TaskType | str | None" = None,
        review: "Review | ReviewType | None" = ReviewUnspecified,
        label: "str | None" = None,
        label_in: "Container[str] | None" = None,
        min_confidence: "float | None" = None,
        max_confidence: "float | None" = None,
        page: "int | None" = None,
        page_in: "Collection[int] | None" = None,
        accepted: "bool | None" = None,
        rejected: "bool | None" = None,
        checked: "bool | None" = None,
        signed: "bool | None" = None,
    ) -> "Self":
        """
        Return a new prediction list containing predictions that match
        all of the specified filters.

        predicate: predictions for which this function returns True.
        document: predictions from this document,
        model: predictions from this model, task type, or name,
        review: predictions from this review or review type,
        label: predictions with this label,
        label_in: predictions with one of these labels,
        min_confidence: predictions with confidence >= this threshold,
        max_confidence: predictions with confidence <= this threshold,
        page: extractions/unbundlings on this page,
        page_in: extractions/unbundlings on one of these pages,
        accepted: extractions that have been accepted,
        rejected: extractions that have been rejected,
        checked: form extractions that are checked,
        signed: form extractions that are signed,
        """
        predicates = []

        if predicate is not None:
            predicates.append(predicate)

        if document is not None:
            predicates.append(lambda prediction: prediction.document == document)

        if model is not None:
            predicates.append(
                lambda prediction: (
                    prediction.model == model
                    or prediction.model.task_type == model
                    or prediction.model.name == model
                )
            )

        if review is not ReviewUnspecified:
            predicates.append(
                lambda prediction: (
                    prediction.review == review
                    or (
                        prediction.review is not None
                        and prediction.review.type == review
                    )
                )
            )

        if label is not None:
            predicates.append(lambda prediction: prediction.label == label)

        if label_in is not None:
            predicates.append(lambda prediction: prediction.label in label_in)

        if min_confidence is not None:
            predicates.append(
                lambda prediction: prediction.confidence >= min_confidence
            )

        if max_confidence is not None:
            predicates.append(
                lambda prediction: prediction.confidence <= max_confidence
            )

        if page is not None:
            predicates.append(
                lambda prediction: (
                    (isinstance(prediction, Extraction) and prediction.page == page)
                    or (isinstance(prediction, Unbundling) and page in prediction.pages)
                )
            )

        if page_in is not None:
            page_in = set(page_in)
            predicates.append(
                lambda prediction: (
                    (isinstance(prediction, Extraction) and prediction.page in page_in)
                    or (
                        isinstance(prediction, Unbundling)
                        and bool(page_in & set(prediction.pages))
                    )
                )
            )

        if accepted is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, Extraction)
                and prediction.accepted == accepted
            )

        if rejected is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, Extraction)
                and prediction.rejected == rejected
            )

        if checked is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, FormExtraction)
                and prediction.checked == checked
            )

        if signed is not None:
            predicates.append(
                lambda prediction: isinstance(prediction, FormExtraction)
                and prediction.signed == signed
            )

        return type(self)(nfilter(predicates, self))

    def accept(self) -> "Self":
        """
        Mark extractions as accepted for auto review.
        """
        self.oftype(Extraction).apply(Extraction.accept)
        return self

    def unaccept(self) -> "Self":
        """
        Mark extractions as not accepted for auto review.
        """
        self.oftype(Extraction).apply(Extraction.unaccept)
        return self

    def reject(self) -> "Self":
        """
        Mark extractions as rejected for auto review.
        """
        self.oftype(Extraction).apply(Extraction.reject)
        return self

    def unreject(self) -> "Self":
        """
        Mark extractions as not rejected for auto review.
        """
        self.oftype(Extraction).apply(Extraction.unreject)
        return self

    def to_changes(self, result: "Result") -> "Any":
        """
        Create a dict or list for the `changes` argument of `SubmitReview` based on the
        predictions in this prediction list and the documents and version of `result`.
        """
        if result.version == 1:
            return self.to_v1_changes(result.documents[0])
        elif result.version == 3:
            return self.to_v3_changes(result.documents)
        else:
            raise ValueError(f"unsupported file version `{result.version!r}`")

    def to_v1_changes(self, document: "Document") -> "dict[str, Any]":
        """
        Create a v1 dict for the `changes` argument of `SubmitReview`.
        """
        changes: "dict[str, Any]" = {}

        for model, predictions in self.groupby(attrgetter("model")).items():
            if model.task_type == TaskType.CLASSIFICATION:
                changes[model.name] = predictions[0].to_v1_dict()
            else:
                changes[model.name] = [
                    prediction.to_v1_dict() for prediction in predictions
                ]

        for model_name in document._model_sections:
            if model_name not in changes:
                changes[model_name] = []

        return changes

    def to_v3_changes(self, documents: "Iterable[Document]") -> "list[dict[str, Any]]":
        """
        Create a v3 list for the `changes` argument of `SubmitReview`.
        """
        changes: "list[dict[str, Any]]" = []

        for document in documents:
            model_results: "dict[str, Any]" = {}
            changes.append(
                {
                    "submissionfile_id": document.id,
                    "model_results": model_results,
                    "component_results": {},
                }
            )
            predictions_by_model = self.where(
                document=document,
            ).groupby(
                attrgetter("model"),
            )

            for model, predictions in predictions_by_model.items():
                model_results[str(model.id)] = [
                    prediction.to_v3_dict() for prediction in predictions
                ]

            for model_id in document._model_sections:
                if model_id not in model_results:
                    model_results[model_id] = []

        return changes
