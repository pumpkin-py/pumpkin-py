import os
from typing import Callable


def register(name: str) -> Callable:
    """Register strawberry.py tracing function.

    This is 'the last resort' option when debugging entangled code.

    Some parts of the code are difficult to debug, by design. One of them being
    spamchannel, for example. For these times, this can be helpful as
    'permanent' solution that stays idle most of the time.

    The usage is like so:

    .. code-block:

        _trace: Callable = pie._tracing.register_trace_function("feature")

    The 'feature' must be registered in 'pie._tracing', otherwise 'ValueError'
    is raised.

    This feature may be enabled by altering environment variables:

    .. code-block:

        trace_pie_spamchannel=1 python3 strawberry.py

    The registration name MUST follow the directory structure:
    'pie_spamchannel', 'modules_base_errors', ...

    When everything goes well, you'll see debug logs printed to the stdout:

    .. code-block:

        Imported database models in 'pie.acl.database'.
        Imported database models in 'pie.i18n.database'.
        Imported database models in 'pie.logger.database'.
        [trace:pie_spamchannel] Function registered.
        Imported database models in 'pie.spamchannel.database'.
        ...
    """
    prefix: str = f"[trace:{name}]"

    if not os.getenv(f"trace_{name}"):
        return lambda *args, **kwargs: None

    def _trace(message: str) -> None:
        print("{prefix} {message}".format(prefix=prefix, message=message))

    _trace("Function registered.")
    return _trace
