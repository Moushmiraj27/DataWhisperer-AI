import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    normalized_level = level.upper()
    if normalized_level not in logging._nameToLevel:
        normalized_level = "INFO"

    logging.basicConfig(
        level=normalized_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
