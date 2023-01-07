class NoInstanceError(Exception):
    """Raised when trying to access an instance, that doesn't exist."""


class DuplicateError(Exception):
    """Raised when there is duplicate entry in database."""


class DivByZeroWarning(Warning):
    pass
