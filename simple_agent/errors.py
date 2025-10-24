"""Custom exceptions for Simple Agent."""


class ToolValidationError(Exception):
    """Raised when tool arguments fail validation before execution.

    This error should be raised during confirmation handlers when validation
    fails. The error message will be passed back to the LLM so it can retry
    with corrected arguments.
    """

    pass
