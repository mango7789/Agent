import logging
import asyncio
from subprocess import Popen, PIPE

logger = logging.getLogger(__name__)


async def start_rq_worker():
    """Start the RQ worker in a subprocess without blocking."""
    worker_process = Popen(["rq", "worker", "default"], stdout=PIPE, stderr=PIPE)
    logger.info("RQ worker started...")
