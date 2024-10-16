import json
from fastapi import HTTPException
import logging
from rich.logging import RichHandler

logging.basicConfig(
       level="INFO",
       format="%(message)s",
       datefmt="[%X]",
       handlers=[RichHandler(rich_tracebacks=True)]
   )

logger = logging.getLogger(__name__)


def process_events(messages: list):
    for msg in messages:
        if msg.role == "Events":
            return json.loads(msg.content)
    return {}

def handle_exception(error):
    print(f"Error: {error}")
    raise HTTPException(status_code=500, detail=str(error))