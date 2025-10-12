# Architecture Decision Record (ADR)

## Title

Track and Report Full Reference Chain in Circular Reference Errors

## Status

Accepted

## Date

2025-10-13

## Context

Following ADR 0003 (Structured Exception Design), `CircularReferenceError` was designed to include structured data about the error. The initial implementation included only the variable name that caused the circular reference:

```python
class CircularReferenceError(EnvResolveError):
    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        super().__init__(f"Circular reference detected: {variable_name}")
```

However, when debugging circular references in complex configurations, users need to see the **full reference chain** that led to the cycle, not just the variable where the cycle was detected.

Example scenario:

```bash
A=${B}
B=${C}
C=${D}
D=${A}  # Cycle here
```

Current error: `"Circular reference detected: A"`

- User doesn't know which variables are involved in the cycle
- Hard to trace back through the reference chain
- Requires manual inspection of all variables to find the loop

Desired error: `"Circular reference detected: A -> B -> C -> D -> A"`

- Clear visualization of the complete cycle
- Easy to identify all variables involved
- Immediate understanding of the problem

## Decision

Extend `CircularReferenceError` to track and report the **full reference chain** that forms the cycle:

```python
class CircularReferenceError(EnvResolveError):
    def __init__(self, variable_name: str, chain: list[str] | None = None):
        self.variable_name = variable_name
        self.chain = chain or []
        chain_str = " -> ".join(self.chain) if self.chain else variable_name
        msg = f"Circular reference detected: {chain_str}"
        super().__init__(msg)
```

**Implementation approach:**

- Maintain a `stack: list[str]` during recursive expansion
- When a variable already in the stack is encountered, extract the cycle portion
- Pass the cycle chain to `CircularReferenceError` constructor
- Format chain as `"A -> B -> C -> A"` in error message

**Algorithm:**

```python
def _resolve(var_name: str, env: dict[str, str], stack: list[str]) -> str:
    if var_name in stack:
        # Found cycle - extract the cycle portion
        cycle_start = stack.index(var_name)
        cycle = [*stack[cycle_start:], var_name]
        raise CircularReferenceError(var_name, cycle)

    stack.append(var_name)
    try:
        return _expand_text(env[var_name], env, stack)
    finally:
        stack.pop()
```

## Rationale

**Why track full chain?**

- **Debugging efficiency**: Users immediately see the problem without manual tracing
- **Error clarity**: Complex cycles (`A -> B -> C -> D -> A`) are instantly visible
- **Actionable information**: Users know exactly which variables to fix

**Why format as "A -> B -> A"?**

- **Visual clarity**: Arrow notation is intuitive and commonly used
- **Cycle visibility**: Showing start and end makes the loop obvious
- **Familiarity**: Matches stack trace and dependency chain conventions

**Why list of strings over single string?**

- **Programmatic access**: Callers can analyze the chain (`len(exc.chain)` for cycle length)
- **Testing**: Can assert specific cycles in tests
- **Future flexibility**: Can format chain differently (JSON, graph, etc.)
- **Consistency**: Follows ADR 0003's principle of structured data over formatted strings

## Implications

### Positive Implications

- **Better user experience**: Errors are immediately actionable
- **Reduced debugging time**: No need to manually trace through variable definitions
- **Professional error messages**: Clear, informative, helpful
- **Testing improvement**: Can verify exact cycle detection logic
- **Programmatic error handling**: Tools can analyze circular dependencies automatically

### Concerns

- **Memory overhead**: Storing chain list for each error
  - Mitigation: Chains are typically 2-10 variables; minimal memory impact
  - Errors are exceptional path, not hot path
- **Stack management complexity**: Need to pass and maintain stack through recursion
  - Mitigation: Stack is implementation detail, not exposed in public API
  - Clear with try/finally pattern
- **Chain extraction logic**: Must correctly identify cycle portion
  - Mitigation: Simple slice operation `stack[cycle_start:]`
  - Well-tested in unit tests

## Alternatives

### Variable Name Only (Original Design)

Keep only `variable_name` without chain:

```python
class CircularReferenceError(EnvResolveError):
    def __init__(self, variable_name: str):
        super().__init__(f"Circular reference detected: {variable_name}")
```

- **Pros**:
  - Simplest implementation
  - Minimal memory usage
  - No stack tracking needed
- **Cons**:
  - Poor debugging experience
  - User must manually trace references
  - Hard to identify long cycles
- **Rejection reason**: Sacrifices usability for minimal complexity reduction

### Full Stack Trace in Error Message

Include full Python stack trace showing function calls:

```python
import traceback
msg = f"Circular reference: {variable_name}\n{traceback.format_stack()}"
```

- **Pros**:
  - Shows complete execution context
  - Includes line numbers and file names
- **Cons**:
  - Cluttered with implementation details (internal function names)
  - Confuses users with irrelevant information
  - Chain is buried in noise
- **Rejection reason**: Too much information, not user-focused

### Lazy Chain Computation

Don't track chain during expansion; recompute if error occurs:

```python
def find_cycle(var_name: str, env: dict[str, str]) -> list[str]:
    # Re-traverse to find cycle
    visited = []
    current = var_name
    while current not in visited:
        visited.append(current)
        current = extract_next_var(env[current])
    return visited[visited.index(current):]
```

- **Pros**:
  - No overhead during normal execution
  - Chain only computed when error occurs
- **Cons**:
  - Complex re-traversal logic
  - May not find exact same cycle (if nested expansion)
  - Requires parsing variable references again
- **Rejection reason**: Complexity outweighs benefits; expansion already maintains stack

### Set-Based Cycle Detection Only

Use a set for fast lookup, don't track order:

```python
visited = set()
if var_name in visited:
    raise CircularReferenceError(var_name, list(visited))
```

- **Pros**:
  - Fast O(1) lookup
  - Simple implementation
- **Cons**:
  - Set is unordered; can't show reference chain in correct order
  - Cycle path is lost (which variables led to which)
  - Error message is confusing: "Circular reference in {C, A, B, D}" (no order)
- **Rejection reason**: Order is critical for understanding the problem

## Future Direction

- **Cycle visualization**: For complex cycles, consider:
  - ASCII art diagram showing the cycle
  - Graphviz DOT format for automated visualization
  - Suggestion of which variable to change

- **Cycle length limits**: If cycles exceed N variables, truncate display:

  ```text
  "Circular reference: A -> B -> ... -> Y -> Z -> A (50 variables in cycle)"
  ```

- **Interactive debugging**: If running in interactive environment:
  - Highlight cycle variables in configuration file
  - Suggest breaking the cycle with environment override

- **Multiple cycle detection**: Currently stops at first cycle found:
  - Consider detecting all cycles in a configuration
  - Report all cycles together for comprehensive fix

- **Performance monitoring**: Track cycle detection overhead:
  - If stack management becomes bottleneck, optimize
  - Consider specialized data structure for large configurations

## References

- ADR 0003: Structured Exception Design (establishes pattern of structured data in exceptions)
- Implementation: `src/envresolve/exceptions.py::CircularReferenceError`
- Implementation: `src/envresolve/services/expansion.py::_resolve`
- Test cases: `tests/unit/test_expansion.py::test_circular_reference_raises_error`
- Graph cycle detection algorithms: https://en.wikipedia.org/wiki/Cycle_detection
- Error message best practices: https://developers.google.com/tech-writing/error-messages
