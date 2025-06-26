import logging

logger = logging.getLogger("illuminator")
logger.setLevel(logging.INFO)

# Don't let it propagate to the root logger (which docling uses)
logger.propagate = False

# Add handler if none exists (to avoid duplication)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
