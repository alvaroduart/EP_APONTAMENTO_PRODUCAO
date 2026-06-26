class BusinessError(Exception):
    """Base class for business exceptions."""
    pass

class OPNotFoundError(BusinessError):
    """Raised when an OP is not found in the base."""
    pass

class OcorrenciaEmAndamentoError(BusinessError):
    """Raised when trying to register production while an occurrence is active."""
    pass
