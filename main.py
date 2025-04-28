import os, uuid, asyncio, logging
import httpx, uvicorn
from rq import Queue
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.params import *
from src.logger import setup_logger, LOGGING_CONFIG
from src.models import ScraperParams, MatcherParams
from src.database import MySQLDatabase
from src.worker import start_rq_worker
from src.scraper import run_scraper


###########################################################
#                   Initialization                        #
###########################################################

# Redis connections
nsync_redis = Redis(host=REDIS_HOST, port=REDIS_POST, decode_responses=True)
async_redis = AsyncRedis(host=REDIS_HOST, port=REDIS_POST, decode_responses=True)

# RQ Queue
scraper_queue = Queue(SCRAPER_QUEUE_KEY, connection=nsync_redis)

# Logger setup
setup_logger()
logger = logging.getLogger(__name__)

# Database connection
mysql_db = MySQLDatabase()


# TODO: Establish a session with the website


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    # Create background tasks
    # asyncio.create_task(start_rq_worker())
    asyncio.create_task(scraper_scheduler())
    # asyncio.create_task(message_monitor())
    # asyncio.create_task(process_message())

    yield

    # Clean up resources
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)


###########################################################
#                       Scraper                           #
###########################################################


async def scraper_scheduler():
    """Continuously schedule pending scraper tasks if slots are available."""
    logger.info("Scraper scheduler started...")

    while True:
        running = int(nsync_redis.get(SCRAPER_RUNNING_TASKS_KEY) or 0)
        if running < MAX_RUNNING_TASKS:
            task_data = nsync_redis.lpop(SCRAPER_PENDING_TASKS_KEY)
            if task_data:
                param1, param2, job_id = task_data.split(",")
                nsync_redis.incr(SCRAPER_RUNNING_TASKS_KEY)
                scraper_queue.enqueue(run_scraper, param1, param2, job_id)
                logger.info(f"Scheduled pending task {job_id}")

        await asyncio.sleep(10)
        if asyncio.current_task().cancelled():
            break


@app.post("/scraper")
async def scraper(scraper_params: ScraperParams):
    """Submit a new scraper task."""
    job_id = str(uuid.uuid4())
    nsync_redis.set(job_id, "Pending")
    nsync_redis.rpush(
        SCRAPER_PENDING_TASKS_KEY,
        f"{scraper_params.param1},{scraper_params.param2},{job_id}",
    )

    logger.info(
        f"Task {job_id} enqueued with params {scraper_params.param1}, {scraper_params.param2}"
    )

    return {
        "message": "Task is queued and will start automatically when possible.",
        "job_id": job_id,
    }


@app.get("/scraper_status/{job_id}")
async def scraper_status(job_id: str):
    """Get the status of a scraper task."""
    status = nsync_redis.get(job_id)
    if status is None:
        return {"status": "None", "message": "Task not found."}
    return {"status": status, "job_id": job_id}


###########################################################
#                     Message Relay                       #
###########################################################


# TODO: This is a mock function of checking new message from website
async def check_new_messages():
    """
    Check if there are any new messages. Return a list of (user_id, message) pairs.
    You can use the provided API of the website if available.
    """
    new_messages = [
        ("user123", "Hello from user123!"),
        ("user456", "Hi, this is user456."),
    ]
    return new_messages


async def detect_new_message():
    """Simulate detecting new messages in a loop."""
    while True:
        await asyncio.sleep(10)
        results = await check_new_messages()
        if results:
            for user_id, message in results:
                yield user_id, message


async def message_monitor():
    """
    Background worker that monitors and detects new messages from an external source.
    """
    logger.info("Message monitor started...")
    async for user_id, message in detect_new_message():
        logger.info(f"New message detected from user {user_id}: {message}")

        await async_redis.rpush(MESSAGE_QUEUE_KEY, f"{user_id}|||{message}")
        logger.info(f"Message pushed to Redis for user {user_id}: {message}")

        if asyncio.current_task().cancelled():
            break


# TODO: This is a mock function of generating response for given message
@app.post("/llm")
async def llm(payload: dict):
    """This endpoint generates a response."""
    message = payload["message"]
    return {"response": f"Echo: {message}"}


async def generate_response(message: str) -> str:
    """Simulate generating a response based on the user's message."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"http://{APP_HOST}:{APP_PORT}/llm", json={"message": message}
        )
        resp.raise_for_status()
        data = resp.json()
        return data["response"]


# TODO: This is a mock function of sending response to the given user
async def send_response(user_id: str, response: str):
    """Send the generated response to the user (mock function)."""
    logger.info(f"[SEND] Responding to user {user_id}: {response}")
    return True


async def process_message():
    """Background worker that listens for new messages and processes them."""
    logger.info("Message worker started...")
    while True:
        data = await async_redis.blpop(MESSAGE_QUEUE_KEY, timeout=0)
        if data:
            _, value = data
            user_id, message = value.split("|||", 1)
            logger.info(f"Processing message from user {user_id}: {message}")

            response = await generate_response(message)

            await send_response(user_id, response)

            await async_redis.rpush(f"user:{user_id}:responses", response)
            logger.info(f"Response generated and saved for user {user_id}: {response}")

        await asyncio.sleep(1)
        if asyncio.current_task().cancelled():
            break


###########################################################
#                          Score                          #
###########################################################


@app.post("matcher")
async def matcher(matcher_params: MatcherParams):
    pass


if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_config=LOGGING_CONFIG)
