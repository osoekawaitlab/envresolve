# ADR 0030: Logging Information Disclosure Boundaries

## Status

Accepted

## Date

2025-11-26

## Context

When implementing logging support (issue #40), we need to establish clear boundaries for what information can be safely logged without exposing sensitive data. The challenge is balancing security (not exposing secrets), debuggability (providing diagnostic information), and compliance (acceptance criteria: no secret values or secret names).

## Decision

Default logging exposes only operation types, success/failure status, and error categories. No specific values are logged by default.

**What Gets Logged:**

- Operation type ("Variable expansion", "Secret resolution")
- Success/failure status
- Error category ("Variable not found", "Circular reference detected", "Provider error")

**What Does NOT Get Logged:**

- Environment variable names, variable names
- Vault names, secret names, URIs
- Resolved values

**Example:**

```python
logger.debug("Variable expansion completed")
logger.error("Variable expansion failed: variable not found")
```

**Future:** An opt-in mechanism for detailed logging will be designed according to the library's principles of fine-grained control and secure defaults.

**Exceptions:** Exception objects contain full details (URIs, vault names, secret names, variable names) for application-level logging decisions.

## Rationale

**Secure by Default:** Even environment variable names can reveal sensitive information (`ADMIN_PASSWORD`, `PROD_API_KEY`). Different applications have different security requirements; the safest default is minimal logging.

**Operation-Level Logging is Sufficient:** Error categories (variable not found, circular reference, provider error) provide enough context for monitoring and alerting. Applications can add correlation IDs via logging filters (`logging.Filter` with `contextvars`), structured logging libraries (e.g., `structlog`), or application-level log context.

**Preserve Details in Exceptions:** Exception objects contain full details for debugging. Application developers can catch exceptions and decide how to log them according to their security policies. This provides secure defaults while preserving flexibility.

## Implications

### Positive Implications

- Logs safe to share and store in less secure systems
- Meets acceptance criteria requirements
- Simple, unambiguous rules
- Exception details provide full information for custom logging

### Concerns

- Minimal debugging information in default logs requires examining exceptions or application-level logging
- Opt-in mechanism for detailed logging not yet implemented (future work)
- **Mitigation:** Exceptions contain full details; applications can implement custom logging by catching exceptions

## Alternatives

### Include Variable/Environment Variable Names

- **Rejected:** Cannot assume names are always safe to log (`ADMIN_PASSWORD`, `PROD_API_KEY`). Opt-in mechanism provides flexibility without compromising default security.

### Include Vault Names

- **Rejected:** Vault names reveal infrastructure details (prod-vault, staging-vault). Developers can access from exception attributes.

### Log Details at Higher Log Levels (TRACE)

- **Rejected:** Log levels are for verbosity, not security boundaries. Security choices should be explicit configuration, not tied to verbosity.

## Future Direction

- **Design opt-in mechanism** for detailed logging (per-instance, per-call, or global) aligned with fine-grained control principles
- **Document best practices** for application-level exception handling and custom logging
- **Monitor usage** to determine if current boundaries are sufficient
- **Consider features**: URI sanitization utilities, metrics/telemetry support

## References

- Issue #40: Add logging support
- OWASP Logging Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
- ADR-0028: Forbid All Implicit Configuration via Environment Variables - Aligns with principle of explicit configuration
