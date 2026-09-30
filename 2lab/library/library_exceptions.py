class DomainError(Exception):
    pass


class InvalidValueObject(DomainError):
    pass


class DomainInvariantViolation(DomainError):
    pass