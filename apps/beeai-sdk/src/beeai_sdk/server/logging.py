import logging

from uvicorn.logging import DefaultFormatter

logger = logging.getLogger("acp")


def configure_logger() -> None:
    """Utility that configures the root logger"""
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()
    handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
