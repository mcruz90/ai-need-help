import json
from fastapi import HTTPException
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install

# Install rich traceback handling
install(show_locals=True)

# Create a console object for rich output
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, show_path=False)]
)

logger = logging.getLogger("ai_assistant")


def process_events(messages: list):
    for msg in messages:
        if msg.role == "Events":
            return json.loads(msg.content)
    return {}

def handle_exception(error):
    logger.error(f"Error: {error}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(error))

def log_structured(log_type: str, message: str, data: dict = None):
    """
    Log a structured message with optional data.
    """
    log_entry = {
        "type": log_type,
        "message": message,
    }
    if data:
        log_entry["data"] = data

    if log_type == "ERROR":
        logger.error(json.dumps(log_entry, indent=2))
    else:
        logger.info(json.dumps(log_entry, indent=2))
