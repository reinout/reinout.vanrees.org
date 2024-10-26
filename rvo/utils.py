import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_if_changed(target: Path, desired_content: str) -> bool:
    """Write content to file if different, not if it is the same

    And create the file if it doesn't exist.

    Return true if created.

    """
    existing_content = target.read_text() if target.exists() else ""

    if desired_content == existing_content:
        logger.debug(f"{target} remained the same")
        return False

    target.write_text(desired_content)
    logger.info(f"Wrote {target}")
    return True
