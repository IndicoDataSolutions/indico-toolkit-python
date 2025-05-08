from collections.abc import Iterable, Iterator
from typing import Callable, TypeVar

Value = TypeVar("Value")


def get(result: object, value_type: "type[Value]", *keys: "str | int") -> Value:
    """
    Return the value of type `value_type` obtained by traversing `result` using `keys`.
    Raise an error if a key doesn't exist or the value has the wrong type.
    """
    for key in keys:
        if isinstance(result, dict):
            if key in result:
                result = result[key]
            else:
                raise KeyError(f"{key!r} not in {result.keys()!r}")
        elif isinstance(result, list):
            if isinstance(key, int):
                if 0 <= key < len(result):
                    result = result[key]
                else:
                    raise IndexError(f"{key} out of range [0,{len(result)})")
            else:
                raise TypeError(f"list can't be indexed with {key!r}")
        else:
            raise TypeError(f"{type(result)} can't be traversed")

    if isinstance(result, value_type):
        return result
    else:
        raise TypeError(f"value `{result!r}` doesn't have type {value_type}")


def has(result: object, value_type: "type[Value]", *keys: "str | int") -> bool:
    """
    Check if `result` can be traversed using `keys` to a value of type `value_type`.
    """
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        elif isinstance(result, list) and isinstance(key, int) and 0 <= key < len(result):  # fmt: skip  # noqa: E501
            result = result[key]
        else:
            return False

    return isinstance(result, value_type)


def nfilter(
    predicates: "Iterable[Callable[[Value], bool]]", values: "Iterable[Value]"
) -> "Iterator[Value]":
    """
    Apply multiple filter predicates to an iterable of values.

    `nfilter([first, second, third], values)` is equivalent to
    `filter(third, filter(second, filter(first, values)))`.
    """
    for predicate in predicates:
        values = filter(predicate, values)

    yield from values


def omit(dictionary: object, *keys: str) -> "dict[str, Value]":
    """
    Return a shallow copy of `dictionary` with `keys` omitted.
    """
    if not isinstance(dictionary, dict):
        return {}
    return {
        key: value
        for key, value in dictionary.items()
        if key not in keys
    }  # fmt: skip
