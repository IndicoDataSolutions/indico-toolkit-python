import pytest

from indico_toolkit.types import (
    ClassificationList,
    Document,
    ExtractionList,
    MultipleValuesError,
    Review,
    ReviewType,
)


class TestDocument:
    @staticmethod
    def test_labels() -> None:
        document = Document._from_v1_result(
            {
                "file_version": 1,
                "submission_id": 11,
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Email": {
                                "pre_review": [
                                    {
                                        "label": "Label A",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                ],
                                "post_reviews": [
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Label B",
                                            "pageNum": 1,
                                        },
                                    ],
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Label C",
                                            "pageNum": 1,
                                        },
                                    ],
                                ],
                                "final": [
                                    {
                                        "text": "47576",
                                        "label": "Label D",
                                        "pageNum": 1,
                                    },
                                ],
                            },
                            "Classification": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Label E",
                                },
                            },
                        },
                    }
                },
            },
            [
                Review(0, 0, None, False, ReviewType.AUTO),
                Review(0, 0, None, False, ReviewType.HITL),
            ],
        )

        assert document.labels == {
            "Label A",
            "Label B",
            "Label C",
            "Label D",
            "Label E",
        }

    @staticmethod
    def test_models() -> None:
        document = Document._from_v1_result(
            {
                "file_version": 1,
                "submission_id": 11,
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Model A": {
                                "pre_review": [
                                    {
                                        "label": "Label A",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                ],
                                "post_reviews": [],
                                "final": [
                                    {
                                        "text": "47576",
                                        "label": "Label D",
                                        "pageNum": 1,
                                    },
                                ],
                            },
                            "Model B": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Label E",
                                },
                            },
                        },
                    }
                },
            },
            [],
        )

        assert document.models == {"Model A", "Model B"}


class TestV1Document:
    @staticmethod
    def test_from_result() -> None:
        document = Document._from_v1_result(
            {
                "file_version": 1,
                "submission_id": 11,
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Email": {
                                "pre_review": [
                                    {
                                        "label": "Insured Name",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                    {
                                        "label": "Broker Contact Name",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "John",
                                    },
                                    {
                                        "label": "Insured Name",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                    {
                                        "label": "Insured Name",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                ],
                                "post_reviews": [
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Broker Zip or Postal Code",
                                            "pageNum": 1,
                                        },
                                        {
                                            "text": "123 Totally Real St",
                                            "label": "Broker Street Address",
                                            "pageNum": 1,
                                        },
                                        {
                                            "text": "CA",
                                            "label": "Broker State",
                                            "pageNum": 1,
                                        },
                                    ],
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Broker Zip or Postal Code",
                                            "pageNum": 1,
                                        },
                                        {
                                            "text": "123 Totally Real St",
                                            "label": "Broker Street Address",
                                            "pageNum": 1,
                                        },
                                    ],
                                ],
                                "final": [
                                    {
                                        "text": "47576",
                                        "label": "Broker Zip or Postal Code",
                                        "pageNum": 1,
                                    },
                                ],
                            },
                            "Classification": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Email",
                                },
                            },
                        },
                    }
                },
            },
            [
                Review(0, 0, None, False, ReviewType.AUTO),
                Review(0, 0, None, False, ReviewType.HITL),
            ],
        )

        assert document.id is None
        assert document.filename is None
        assert document.etl_output == "indico-file:///etl_output.json"
        assert document.classification.label == "Email"
        assert document.subdocuments == []
        assert isinstance(document.classifications, ClassificationList)
        assert len(document.classifications) == 1
        assert isinstance(document.pre_review, ExtractionList)
        assert len(document.pre_review) == 4
        assert isinstance(document.auto_review, ExtractionList)
        assert len(document.auto_review) == 3
        assert isinstance(document.hitl_review, ExtractionList)
        assert len(document.hitl_review) == 2
        assert isinstance(document.final, ExtractionList)
        assert len(document.final) == 1

    @staticmethod
    def test_no_classification() -> None:
        document = Document._from_v1_result(
            {
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {},
                    },
                },
            },
            [],
        )

        with pytest.raises(MultipleValuesError):
            document.classification

    @staticmethod
    def test_multiple_classification() -> None:
        document = Document._from_v1_result(
            {
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Classification A": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Email",
                                },
                                "post_reviews": [],
                                "final": {
                                    "confidence": {},
                                    "label": "Email",
                                },
                            },
                            "Classification B": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Email",
                                },
                                "post_reviews": [],
                                "final": {
                                    "confidence": {},
                                    "label": "Email",
                                },
                            },
                        },
                    }
                },
            },
            [],
        )

        with pytest.raises(MultipleValuesError):
            document.classification

    @staticmethod
    def test_labels() -> None:
        document = Document._from_v1_result(
            {
                "file_version": 1,
                "submission_id": 11,
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Email": {
                                "pre_review": [
                                    {
                                        "label": "Label A",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                ],
                                "post_reviews": [
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Label B",
                                            "pageNum": 1,
                                        },
                                    ],
                                    [
                                        {
                                            "text": "47576",
                                            "label": "Label C",
                                            "pageNum": 1,
                                        },
                                    ],
                                ],
                                "final": [
                                    {
                                        "text": "47576",
                                        "label": "Label D",
                                        "pageNum": 1,
                                    },
                                ],
                            },
                            "Classification": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Label E",
                                },
                            },
                        },
                    }
                },
            },
            [
                Review(0, 0, None, False, ReviewType.AUTO),
                Review(0, 0, None, False, ReviewType.HITL),
            ],
        )

        assert document.labels == {
            "Label A",
            "Label B",
            "Label C",
            "Label D",
            "Label E",
        }

    @staticmethod
    def test_models() -> None:
        document = Document._from_v1_result(
            {
                "file_version": 1,
                "submission_id": 11,
                "etl_output": "indico-file:///etl_output.json",
                "results": {
                    "document": {
                        "results": {
                            "Model A": {
                                "pre_review": [
                                    {
                                        "label": "Label A",
                                        "confidence": {},
                                        "page_num": 0,
                                        "text": "MICHAEL WELBORN SERVICES, INC",
                                    },
                                ],
                                "post_reviews": [],
                                "final": [
                                    {
                                        "text": "47576",
                                        "label": "Label D",
                                        "pageNum": 1,
                                    },
                                ],
                            },
                            "Model B": {
                                "pre_review": {
                                    "confidence": {},
                                    "label": "Label E",
                                },
                            },
                        },
                    }
                },
            },
            [],
        )

        assert document.models == {"Model A", "Model B"}
