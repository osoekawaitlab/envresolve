# Public API

This section covers the main functions intended for direct use in your applications.

## Logging Support

All public API functions and `EnvResolver` methods accept an optional `logger` parameter for diagnostic logging. See the [Logging Guide](../user-guide/logging.md) for details.

```python
import logging
import envresolve

logger = logging.getLogger(__name__)
result = envresolve.resolve_secret("${SECRET}", logger=logger)
```

::: envresolve.api
