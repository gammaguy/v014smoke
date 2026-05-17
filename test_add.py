import inspect

import pytest

from add import add


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),
        (0, 0, 0),
        (-4, -6, -10),
        (-7, 3, -4),
        (1_000_000, 2_000_000, 3_000_000),
    ],
)
def test_add_returns_integer_sum(a: int, b: int, expected: int) -> None:
    result = add(a, b)

    assert result == expected
    assert type(result) is int


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (5, 9),
        (-12, 7),
        (0, 44),
    ],
)
def test_add_is_commutative(a: int, b: int) -> None:
    assert add(a, b) == add(b, a)


@pytest.mark.parametrize("a", [0, 8, -8, 10**50])
def test_add_zero_identity(a: int) -> None:
    assert add(a, 0) == a


@pytest.mark.parametrize(
    ("a", "b", "message"),
    [
        ("1", 2, "a must be int"),
        (2, "1", "b must be int"),
        (1.0, 2, "a must be int"),
        (1, 2.0, "b must be int"),
        (True, 1, "a must be int"),
        (1, False, "b must be int"),
        (None, None, "a must be int"),
        ([], 2, "a must be int"),
        (2, [], "b must be int"),
    ],
)
def test_add_rejects_non_strict_int_inputs(a: object, b: object, message: str) -> None:
    with pytest.raises(TypeError, match=f"^{message}$"):
        add(a, b)


def test_add_signature() -> None:
    signature = inspect.signature(add)

    assert list(signature.parameters) == ["a", "b"]
    assert signature.parameters["a"].annotation is int
    assert signature.parameters["b"].annotation is int
    assert signature.return_annotation is int
