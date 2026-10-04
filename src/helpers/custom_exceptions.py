import sys


class SkipRowException(Exception):
    """Exception to signal that a row should be skipped and marked as finished."""
    pass


class PatientNotFoundException(Exception):
    """Exception raised when a patient is not found across all examination statuses."""
    pass


# Ensure both "custom_exceptions" and "src.helpers.custom_exceptions" point to the same module in sys.modules
if __name__ in sys.modules:
    sys.modules.setdefault("custom_exceptions", sys.modules[__name__])
    sys.modules.setdefault("src.helpers.custom_exceptions", sys.modules[__name__])