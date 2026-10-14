class DomainError(Exception):
    pass


class InvalidValueObject(DomainError):
    pass


class DomainInvariantViolation(DomainError):
    pass


class TransitionNotAllowed(DomainError):
    pass


class GatewayUnresolved(DomainError):
    pass