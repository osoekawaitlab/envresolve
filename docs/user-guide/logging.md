# Logging

envresolve provides built-in logging support to help you debug resolution issues and monitor secret access in production.

## Why Logging?

Logging helps you:

- Debug why a variable isn't resolving correctly
- Understand which secrets are being accessed and when
- Troubleshoot performance issues
- Audit secret access for security compliance

## Basic Usage

### With EnvResolver

Pass a logger to the `EnvResolver` constructor:

```python
import logging
from envresolve import EnvResolver

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create resolver with logger
resolver = EnvResolver(logger=logger)
result = resolver.resolve_secret("${DATABASE_URL}")
```

### With Global Facade

You have two options with the global facade:

#### Option 1: Set Global Default Logger

```python
import logging
import envresolve

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set global default logger
envresolve.set_logger(logger)

# All subsequent calls use the global logger
result = envresolve.resolve_secret("${DATABASE_URL}")
```

#### Option 2: Override Per-Call

```python
import logging
import envresolve

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Override logger for specific call
result = envresolve.resolve_secret("${DATABASE_URL}", logger=logger)
```

## What Gets Logged

envresolve logs operations with:

- **Operation type**: "Variable expansion", "Secret resolution"
- **Success/failure status**: "completed", "failed"
- **Error category**: "variable not found", "circular reference detected", "provider error"

### Example Log Output

**Successful resolution:**
```
DEBUG - Variable expansion completed
DEBUG - Secret resolution completed
```

**Failed resolution:**
```
ERROR - Variable expansion failed: variable not found
```

## What Does NOT Get Logged

By default, envresolve **does not log**:

- Environment variable names
- Variable names
- Vault names
- Secret names
- URIs
- Resolved values

This protects sensitive information from appearing in logs. See [Security Considerations](#security-considerations) for details.

## Common Logging Setups

### Development: Console Logging

```python
import logging
import envresolve

# Simple console logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

envresolve.set_logger(logger)
```

### Production: File Logging

```python
import logging
import envresolve

# File-based logging for production
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/var/log/myapp/envresolve.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

envresolve.set_logger(logger)
```

### Production: JSON Logging with structlog

```python
import logging
import structlog
import envresolve

# Structured JSON logging with structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
envresolve.set_logger(logger)
```

### Production: Error-Only Logging

```python
import logging
import envresolve

# Log only errors in production
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

envresolve.set_logger(logger)
```

### Testing: Capturing Logs

```python
import logging
from envresolve import EnvResolver

def test_secret_resolution():
    # Use pytest's caplog fixture or Python's logging.handlers.MemoryHandler
    logger = logging.getLogger("test")
    handler = logging.handlers.MemoryHandler(capacity=100)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    resolver = EnvResolver(logger=logger)
    result = resolver.resolve_secret("plain-text")

    # Verify logs
    handler.flush()
    records = handler.buffer
    assert any("Variable expansion completed" in r.message for r in records)
```

## Per-Method Logger Override

You can override the logger for individual method calls:

```python
import logging
from envresolve import EnvResolver

# Constructor logger
default_logger = logging.getLogger("default")
resolver = EnvResolver(logger=default_logger)

# Override for specific call
special_logger = logging.getLogger("special")
result = resolver.resolve_secret("${SECRET}", logger=special_logger)
```

## Security Considerations

### What's Safe to Log

envresolve's default logging is designed to be **safe for general-purpose logging systems** that may:

- Be stored in less secure environments
- Be accessible to multiple teams
- Be retained long-term
- Be shared for debugging

The operation-level logging (type, status, error category) provides enough information for:

- Monitoring and alerting
- Detecting configuration issues
- Troubleshooting resolution failures

### What's NOT Safe by Default

By design, envresolve **does not log**:

- Variable names (could reveal `ADMIN_PASSWORD`, `PROD_API_KEY`)
- Vault names (could reveal infrastructure: `prod-vault`, `staging-vault`)
- Secret names (could reveal what secrets exist)
- URIs (could reveal secret locations)
- Resolved values (would expose secrets themselves)

### Exception Details

While logs are minimal, **exception objects contain full details**:

```python
import envresolve

try:
    result = envresolve.resolve_secret("${MISSING_VAR}")
except envresolve.VariableNotFoundError as e:
    # Exception has full details
    print(f"Variable not found: {e.variable_name}")

    # You can decide what to log
    logger.error(f"Resolution failed for ${{{e.variable_name}}}")
```

This lets you implement custom logging based on your security requirements.

### Application-Level Logging

For more detailed logging, catch exceptions and log at the application level:

```python
import logging
import envresolve

logger = logging.getLogger(__name__)

try:
    result = envresolve.resolve_secret("${DATABASE_URL}")
except envresolve.VariableNotFoundError as e:
    # Log with context appropriate for your security policy
    logger.error(
        "Failed to resolve environment variable",
        extra={
            "variable": e.variable_name,
            "context": "database_config"
        }
    )
    raise
```

## Advanced: Correlation IDs

Add correlation IDs using logging filters:

```python
import logging
import contextvars
import envresolve

# Context variable for request ID
request_id_var = contextvars.ContextVar('request_id', default=None)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# Set up logger with filter
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.addFilter(RequestIdFilter())
formatter = logging.Formatter(
    '%(asctime)s - %(request_id)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

envresolve.set_logger(logger)

# Use in request handler
def handle_request(request):
    request_id_var.set(request.id)
    config = envresolve.load_env()
    # Logs will include request_id
```

## Performance

When no logger is provided, logging has **zero performance impact**. The implementation uses simple `if logger is not None` checks that have negligible overhead.

## See Also

- [ADR-0029: Logger Propagation Through Layers](../adr/0029-logger-propagation-through-layers.md)
- [ADR-0030: Logging Information Disclosure Boundaries](../adr/0030-logging-information-disclosure-boundaries.md)
