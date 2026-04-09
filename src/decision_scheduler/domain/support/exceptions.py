# exceptions.py

class DomainError(Exception):
    """Base class for all domain-related errors."""
    pass

class SchedulingException(DomainError):
    pass

class InvalidTaskInitError(DomainError):
    """Raised when TaskInit violates preconditions."""
    pass

class InvalidActionError(DomainError):
    """Raised when an invalid action is applied to the state."""
    pass

class TransitionRegistrationError(DomainError):
    """Raised when there is an error during runtime handler registration."""
    pass

class TransitionFrozenError(DomainError):
    """Raised when attempting to modify a frozen transition."""
    pass

class UnknownActionHandlerError(DomainError):
    """Raised when no handler is found for a given action."""
    pass