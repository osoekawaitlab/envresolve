# ADR 0006: Two-Phase Iterative Algorithm for Nested Variable Expansion

## Status

Accepted

## Date

2025-10-13

## Context

The variable expansion service needs to support nested variable references like `${VAR_${NESTED}}`, where variable names themselves contain variable references that must be resolved first. This enables dynamic construction of variable names based on runtime values.

Example use case:

```bash
ENV=prod
DB_HOST=${DB_HOST_${ENV}}  # Should resolve to ${DB_HOST_prod}
DB_HOST_prod=prod-server.example.com
```

Key requirements:

- Support arbitrary nesting depth (`${A_${B_${C}}}`)
- Maintain backward compatibility with simple expansion
- Detect circular references at any nesting level
- Provide clear error messages
- Acceptable performance for typical use cases

Algorithm choices:

1. **Single-pass recursive regex**: Replace variables recursively until no matches remain
2. **Two-phase iterative**: Expand innermost curly braces first, then simple variables
3. **AST-based parser**: Build syntax tree, evaluate bottom-up
4. **Multi-pass until stable**: Keep expanding until output stops changing

## Decision

Use a **two-phase iterative algorithm** that processes variables in phases:

### Phase 1: Innermost Curly Braces

- Pattern: `\$\{([^{}]+)\}` (no nested braces)
- Expand innermost `${VAR}` references first
- Repeat until no more innermost curly braces match

### Phase 2: Simple Variables

- Pattern: `\$([A-Za-z_][A-Za-z0-9_]*)\b`
- Expand `$VAR` syntax
- Repeat until no more simple variables match

**Algorithm:**

```python
def _expand_text(value: str, env: dict[str, str], stack: list[str]) -> str:
    current = value
    while True:
        # Phase 1: Expand innermost curly braces
        if INNER_CURLY_PATTERN matches:
            current = expand matches with _resolve()
            continue

        # Phase 2: Expand simple variables
        if SIMPLE_VAR_PATTERN matches:
            current = expand matches with _resolve()
            continue

        # No more matches - done or error
        if unresolved patterns remain:
            raise VariableNotFoundError
        return current
```

## Rationale

**Why two-phase?**

- **Correctness**: Innermost-first ensures nested references resolve correctly
- **Predictability**: Clear evaluation order (inside-out, left-to-right within phase)
- **Error detection**: Unresolved patterns after both phases indicate missing variables

**Why iterative over recursive?**

- **Stack safety**: No recursion depth limits for deeply nested expressions
- **Debuggability**: Easier to trace expansion steps
- **Performance**: Avoids function call overhead for simple cases

**Why separate phases?**

- **Ambiguity resolution**: `$VAR_${NESTED}` - which part expands first?
- **Backward compatibility**: Simple `${VAR}` and `$VAR` work as before
- **Error clarity**: Can distinguish between syntax errors and missing variables

## Implications

### Positive Implications

- **Enables dynamic variable names**: Powerful pattern for environment-specific configuration
- **Maintains simplicity**: Core algorithm remains understandable
- **Preserves performance**: Only iterates when variables are actually present
- **Clear semantics**: Inside-out evaluation matches user intuition

### Concerns

- **Performance**: Deeply nested variables require multiple passes
    - Mitigation: Most real-world usage is 1-2 levels deep; still O(n*m) where m is nesting depth
- **Pattern ambiguity**: `${VAR${NESTED}}` (missing underscore) is syntactically valid but confusing
    - Mitigation: Document best practices; users should use `${VAR_${NESTED}}`
- **Infinite loop risk**: Pattern must make progress each iteration
    - Mitigation: Iteration only continues if pattern matched; unresolved patterns raise errors

## Alternatives

### Single-Pass Recursive Regex

Recursively expand all variables in one pass:

```python
pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"
re.sub(pattern, replace_func, text)
```

- **Pros**: Simple implementation, single pass
- **Cons**:
    - Cannot handle nested braces correctly
    - `${VAR_${NESTED}}` - inner `${NESTED}` not matched by `[^}]+`
    - Would need complex lookahead/lookbehind patterns
- **Rejection reason**: Regex cannot elegantly handle nested structures

### AST-Based Parser

Build abstract syntax tree, evaluate bottom-up:

```python
ast = parse("${VAR_${NESTED}}")
# → BraceExpansion(
#     name=Concat([Literal("VAR_"), BraceExpansion(name="NESTED")])
#   )
result = evaluate(ast, env)
```

- **Pros**:
    - Very explicit structure
    - Easy to add features (filters, default values)
    - Excellent error reporting with positions
- **Cons**:
    - Significant complexity overhead
    - Requires lexer, parser, evaluator
    - Overkill for current feature set
- **Rejection reason**: Complexity not justified for variable expansion use case

### Multi-Pass Until Stable

Keep expanding until output stops changing:

```python
while True:
    new_value = expand_once(current, env)
    if new_value == current:
        break
    current = new_value
```

- **Pros**: Handles any nesting depth automatically
- **Cons**:
    - Risk of infinite loops if pattern produces itself
    - Harder to detect true errors vs. stability
    - No clear phase ordering for mixed syntax
- **Rejection reason**: Less predictable behavior, harder error handling

### Greedy Regex with Backtracking

Use greedy matching with backtracking for nested patterns:

```python
pattern = r"\$\{([^{}]|\{[^{}]*\})*\}"
```

- **Pros**: Single regex pattern
- **Cons**:
    - Regex complexity explodes with nesting depth
    - Poor error messages on mismatch
    - Performance degrades with deep nesting (catastrophic backtracking risk)
- **Rejection reason**: Regex is wrong tool for nested structures

## Future Direction

- **Performance optimization**: If profiling shows issues, consider:
    - Compile patterns once (already done with module-level `re.compile`)
    - Add depth limit to prevent pathological cases
    - Cache expansion results for repeated patterns

- **Enhanced error messages**: Show partial expansion state when errors occur:

  ```python
  VariableNotFoundError: MISSING
  During expansion of: "${DB_${ENV}}" → "${DB_prod}" → "${DB_prod_MISSING}"
  ```

- **Syntax extensions**: If needed, two-phase algorithm can be extended:
    - Default values: `${VAR:-default}`
    - Filters: `${VAR|lowercase}`
    - Escape sequences: `\${NOT_A_VAR}`

- **Migration to AST**: If feature set grows significantly (10+ syntax features), consider AST-based approach for maintainability

## References

- ADR 0001: Regular expressions for variable expansion
- ADR 0004: Stateless function-based variable expansion
- Implementation: `src/envresolve/services/expansion.py`
- Test cases: `tests/unit/test_expansion.py::test_expand_nested_curly_braces`
- Bash variable expansion: <https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html>
