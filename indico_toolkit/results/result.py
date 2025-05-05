from dataclasses import dataclass
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING

from . import predictions as prediction
from .document import Document
from .errors import ResultError
from .model import ModelGroup
from .normalization import normalize_v1_result, normalize_v3_result
from .predictionlist import PredictionList
from .predictions import Prediction
from .review import Review, ReviewType
from .utils import get, has

if TYPE_CHECKING:
    from typing import Any


@dataclass(frozen=True, order=True)
class Result:
    version: int
    submission_id: int
    documents: "tuple[Document, ...]"
    models: "tuple[ModelGroup, ...]"
    predictions: "PredictionList[Prediction]"
    reviews: "tuple[Review, ...]"

    @property
    def rejected(self) -> bool:
        return len(self.reviews) > 0 and self.reviews[-1].rejected

    @property
    def pre_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=None)

    @property
    def auto_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.AUTO)

    @property
    def manual_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.MANUAL)

    @property
    def admin_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.ADMIN)

    @property
    def final(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=self.reviews[-1] if self.reviews else None)

    @staticmethod
    def from_v1_dict(result: object) -> "Result":
        """
        Create a `Result` from a v1 result file dictionary.
        """
        normalize_v1_result(result)

        version = get(result, int, "file_version")
        submission_id = get(result, int, "submission_id")
        submission_results = get(result, dict, "results", "document", "results")
        review_metadata = get(result, list, "reviews_meta")

        document = Document.from_v1_dict(result)
        models = sorted(map(ModelGroup.from_v1_section, submission_results.items()))
        predictions: "PredictionList[Prediction]" = PredictionList()
        # Reviews must be sorted after parsing predictions, as they match positionally
        # with prediction lists in `post_reviews`.
        reviews = list(map(Review.from_dict, review_metadata))

        for model_name, model_predictions in submission_results.items():
            model = next(filter(lambda model: model.name == model_name, models))
            reviewed_model_predictions: "list[tuple[Review | None, Any]]" = [
                (None, get(model_predictions, list, "pre_review")),
                *filter(
                    lambda review_predictions: not review_predictions[0].rejected,
                    zip(reviews, get(model_predictions, list, "post_reviews")),
                ),
            ]

            for review, model_predictions in reviewed_model_predictions:
                predictions.extend(
                    map(
                        partial(prediction.from_v1_dict, document, model, review),
                        model_predictions,
                    )
                )

        return Result(
            version=version,
            submission_id=submission_id,
            documents=(document,),
            models=tuple(models),
            predictions=predictions,
            reviews=tuple(sorted(reviews)),
        )

    @staticmethod
    def from_v3_dict(result: object) -> "Result":
        """
        Create a `Result` from a v3 result file dictionary.
        """
        normalize_v3_result(result)

        version = get(result, int, "file_version")
        submission_id = get(result, int, "submission_id")
        submission_results = get(result, list, "submission_results")
        modelgroup_metadata = get(result, dict, "modelgroup_metadata")
        component_metadata = get(result, dict, "component_metadata")
        review_metadata = get(result, dict, "reviews")
        errored_files = get(result, dict, "errored_files").values()

        static_model_components = filter(
            lambda component: (
                get(component, str, "component_type").casefold() == "static_model"
            ),
            component_metadata.values(),
        )

        documents = sorted(
            chain(
                map(Document.from_v3_dict, submission_results),
                map(Document.from_v3_errored_file, errored_files),
            )
        )
        models = sorted(
            chain(
                map(ModelGroup.from_v3_dict, modelgroup_metadata.values()),
                map(ModelGroup.from_v3_dict, static_model_components),
            )
        )
        reviews = sorted(map(Review.from_dict, review_metadata.values()))

        predictions: "PredictionList[Prediction]" = PredictionList()

        for document_dict in submission_results:
            document_id = get(document_dict, int, "submissionfile_id")
            document = next(
                filter(lambda document: document.id == document_id, documents)
            )
            reviewed_model_predictions: "list[tuple[Review | None, Any]]" = [
                (None, get(document_dict, dict, "model_results", "ORIGINAL"))
            ]
            reviewed_component_predictions: "list[tuple[Review | None, Any]]" = [
                (None, get(document_dict, dict, "component_results", "ORIGINAL"))
            ]

            if reviews:
                reviewed_model_predictions.append(
                    (reviews[-1], get(document_dict, dict, "model_results", "FINAL"))
                )
                reviewed_component_predictions.append(
                    (reviews[-1], get(document_dict, dict, "component_results", "FINAL"))  # fmt: skip  # noqa: E501
                )

            for review, model_section in reviewed_model_predictions:
                for model_id, model_predictions in model_section.items():
                    model = next(
                        filter(lambda model: model.id == int(model_id), models)
                    )
                    predictions.extend(
                        map(
                            partial(prediction.from_v3_dict, document, model, review),
                            model_predictions,
                        )
                    )

            for review, component_section in reviewed_component_predictions:
                for component_id, component_predictions in component_section.items():
                    try:
                        model = next(
                            filter(lambda model: model.id == int(component_id), models)
                        )
                    except StopIteration:
                        if has(component_metadata, str, component_id, "component_type"):
                            component_type = get(
                                component_metadata, str, component_id, "component_type"
                            )
                            raise ResultError(
                                f"unsupported component type {component_type!r} "
                                f"for component {component_id}"
                            )
                        else:
                            raise ResultError(
                                f"no component metadata for component {component_id}"
                            )

                    predictions.extend(
                        map(
                            partial(prediction.from_v3_dict, document, model, review),
                            component_predictions,
                        )
                    )

        return Result(
            version=version,
            submission_id=submission_id,
            documents=tuple(documents),
            models=tuple(models),
            predictions=predictions,
            reviews=tuple(reviews),
        )
