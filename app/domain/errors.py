"""Domain exceptions decoupled from HTTP transport details."""


class DomainError(Exception):
    """Base domain exception."""


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class SlotConflictError(DomainError):
    """Raised when a booking overlaps an active reservation slot."""
