# exceptions.py

class DomainError(Exception):
    """Base class for all domain-related errors."""
    pass

class SchedulingException(DomainError):
    pass

class InvalidTaskInitError(DomainError):
    """Raised when TaskInit violates preconditions."""
    pass