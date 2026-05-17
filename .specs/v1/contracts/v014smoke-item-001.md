---
lineage:
  contract_id: v014smoke-item-001
  root_spec: v1
  parent_issue: null
  created_via: decomp
  tier: standard

name: add
location: add.py

inputs:
  a:
    type: int
    semantics: The first integer addend. Must be a strict int (bool is not accepted).
  b:
    type: int
    semantics: The second integer addend. Must be a strict int (bool is not accepted).

outputs:
  type: int
  semantics: The arithmetic sum of a and b, computed as a + b.

invariants:
  - "add(a, b) equals a + b for all int inputs a, b within Python's unbounded int range."
  - "add(a, b) equals add(b, a) — commutativity holds because integer addition is commutative."
  - "add(a, 0) equals a for every int a — zero is the additive identity."
  - "add returns a value of type int; never returns float, bool, or any other type."

errors:
  - input: 'a is not an int (e.g., a is a str, float, list, None)'
    behavior: 'raise TypeError("a must be int")'
  - input: 'b is not an int (e.g., b is a str, float, list, None)'
    behavior: 'raise TypeError("b must be int")'
  - input: 'a is a bool (True/False)'
    behavior: 'raise TypeError("a must be int") — bool is rejected even though bool is a subclass of int in Python'
  - input: 'b is a bool (True/False)'
    behavior: 'raise TypeError("b must be int") — bool is rejected even though bool is a subclass of int in Python'

non_goals:
  - This contract does NOT include package structure — no pyproject.toml, no src/ layout, no __init__.py.
  - This contract does NOT include a CLI wrapper or entry point.
  - This contract does NOT include additional arithmetic operations (subtract, multiply, divide).
  - This contract does NOT include type coercion — strings like "3" are rejected with TypeError, not parsed.
  - This contract does NOT define a custom exception subclass — plain TypeError is raised.

decisions:
  - description: "Strict int check via type(x) is int over isinstance(x, int) because isinstance accepts bool (True is 1), which would silently allow add(True, False) to return 1."
  - description: "Plain TypeError over a custom exception subclass because the spec scope_notes explicitly excludes custom exception subclasses."
  - description: "Single source file add.py at project root over a package layout because spec scope_notes explicitly excludes package structure."
  - description: "Parametrized pytest cases via pytest.mark.parametrize over separate test functions because the spec scope_notes requires parametrized fixtures."
  - description: "Rewrote the test-suite acceptance criterion to use the testable verb 'contains' enumerating the four required parametrized case categories, resolving schema_validator blocker from cycle 1 about missing testable verb."

acceptance:
  - "add(2, 3) returns 5 and add(0, 0) returns 0 — positive and zero integer cases produce a + b."
  - "add(-4, -6) returns -10 and add(-7, 3) returns -4 — negative and mixed-sign integer cases produce a + b."
  - "add('1', 2) raises TypeError and add(2, '1') raises TypeError — non-int argument in either position is rejected."
  - "add(1.0, 2) raises TypeError and add(1, 2.0) raises TypeError — float arguments are rejected, no coercion occurs."
  - "add(True, 1) raises TypeError and add(1, False) raises TypeError — bool arguments are rejected despite bool being a subclass of int."
  - "test_add.py contains at least one pytest.mark.parametrize decorator and contains parametrized cases covering each of: positive integers, negative integers, zero, and TypeError on non-int input."
  - "add.py produces a module-level callable named add with signature add(a: int, b: int) -> int."

---

# Examples

| Input | Output |
| ----- | ------ |
| `add(2, 3)` | `5` |
| `add(-4, -6)` | `-10` |
| `add(0, 0)` | `0` |
| `add(-7, 3)` | `-4` |
| `add(1000000, 2000000)` | `3000000` |
| `add('1', 2)` | `raises TypeError("a must be int")` |
| `add(2, '1')` | `raises TypeError("b must be int")` |
| `add(1.5, 2)` | `raises TypeError("a must be int")` |
| `add(True, 1)` | `raises TypeError("a must be int")` |
| `add(None, None)` | `raises TypeError("a must be int")` |