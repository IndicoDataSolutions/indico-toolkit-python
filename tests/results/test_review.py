from indico_toolkit.results import Review


def test_from_dict_defaults_missing_review_rejected_to_false() -> None:
    review = Review.from_dict(
        {
            "review_id": 1,
            "reviewer_id": 2,
            "review_notes": "",
            "review_type": "manual",
        }
    )
    assert review.rejected is False
