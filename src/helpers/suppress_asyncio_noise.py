import logging


class SuppressTargetClosedFilter(logging.Filter):
    """Filter out benign Playwright TargetClosedError warnings emitted during shutdown/GC."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if (
            "TargetClosedError" in message
            or "Target page, context or browser has been closed" in message
        ):
            return False
        if record.exc_info and any(
            isinstance(arg, BaseException) and "TargetClosedError" in type(arg).__name__
            for arg in record.exc_info[:2]
            if arg is not None
        ):
            return False
        return True


def install_asyncio_exception_filter() -> None:
    """Install logging filter on asyncio logger to suppress unretrieved TargetClosedError."""
    logger = logging.getLogger("asyncio")
    for existing_filter in logger.filters:
        if isinstance(existing_filter, SuppressTargetClosedFilter):
            return
    logger.addFilter(SuppressTargetClosedFilter())
