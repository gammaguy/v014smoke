def add(a: int, b: int) -> int:
    """Return the arithmetic sum of two strict integers."""
    if type(a) is not int:
        raise TypeError("a must be int")
    if type(b) is not int:
        raise TypeError("b must be int")
    return a + b
