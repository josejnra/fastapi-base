import json
import sys
from typing import TYPE_CHECKING

from loguru import logger

from app.core.config import get_settings

if TYPE_CHECKING:
    from loguru import Record


def serialize(record: "Record") -> str:
    subset = {
        "timestamp": record["time"].timestamp(),
        "message": record["message"],
        "level": record["level"].name,
        "file": record["file"].name,
        "context": record["extra"],
    }
    return json.dumps(subset)


def patching(record: "Record") -> None:
    record["extra"]["serialized"] = serialize(record)


logger.remove(0)  # remove the default handler configuration

settings = get_settings()
logger = logger.patch(patching)
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="[{time:YYYY-MM-DD HH:mm:ss.SSS}] [{name}:{line}] [{level}] - {message}",
    colorize=True,
    enqueue=True,
)

logger.add(
    "app.log",
    rotation="5 MB",
    format="{extra[serialized]}",
    level=settings.LOG_LEVEL,
    enqueue=True,
)
