# utils/exceptions.py

class OCDBError(Exception):
    """Base exception for all OCDB-related errors."""
    pass


class ConfigError(OCDBError):
    """Raised when configuration is missing or invalid."""
    pass


class DatabaseError(OCDBError):
    """Raised for any database connection or query issues."""
    pass


class AuthError(OCDBError):
    """Raised when authentication / API key validation fails."""
    pass


class NotFoundError(OCDBError):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(OCDBError):
    """Raised when user input or payload is invalid."""
    pass
