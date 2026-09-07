"""Domain-facing errors with stable HTTP semantics."""


class DomainError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)
