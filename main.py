import os, uuid, asyncio, logging
import uvicorn
from pydantic import BaseModel
from rq import Queue
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.params import *
from src.logger import setup_logger
from src.database import MySQLDatabase
from src.scraper import run_scraper


# Redis connections
nsync_redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
async_redis = AsyncRedis(host="localhost", port=6379, db=0, decode_responses=True)

# RQ Queue
scraper_queue = Queue(connection=nsync_redis)

# Logger setup
setup_logger()

# Database connection
mysql_db = MySQLDatabase()

###########################################################
#                   Initialization                        #
###########################################################

# TODO: Establish a session with the website


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""

    log_dir = "./logs/scraper/"
    os.makedirs(log_dir, exist_ok=True)

    # Create background tasks
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


class ScraperParams(BaseModel):
    param1: str
    param2: str


async def scraper_scheduler():
    """Continuously schedule pending scraper tasks if slots are available."""
    logging.info("Scraper scheduler started...")

    while True:
        running = int(nsync_redis.get(SCRAPER_RUNNING_TASKS_KEY) or 0)
        if running < MAX_RUNNING_TASKS:
            task_data = nsync_redis.lpop(SCRAPER_PENDING_TASKS_KEY)
            if task_data:
                param1, param2, job_id = task_data.split(",")
                nsync_redis.incr(SCRAPER_RUNNING_TASKS_KEY)
                scraper_queue.enqueue(run_scraper, param1, param2, job_id)
                logging.info(f"Scheduled pending task {job_id}")

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

    logging.info(
        f"[{job_id}] enqueued with params {scraper_params.param1}, {scraper_params.param2}"
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


# TODO: This is a mock function of detecting new message from website
async def detect_new_message():
    """Simulate detecting new messages in a loop."""
    while True:
        await asyncio.sleep(10)
        user_id = "user123"
        message = "Hello, this is a new message!"
        yield user_id, message


async def message_monitor():
    """
    Background worker that monitors and detects new messages from an external source.
    """
    logging.info("Message monitor started...")
    async for user_id, message in detect_new_message():
        logging.info(f"New message detected from user {user_id}: {message}")

        await async_redis.rpush("message_queue", f"{user_id}|||{message}")
        logging.info(f"Message pushed to Redis for user {user_id}: {message}")

        await asyncio.sleep(10)
        if asyncio.current_task().cancelled():
            break


# TODO: This is a mock function of generating response for given message
async def generate_response(message: str) -> str:
    """Simulate generating a response based on the user's message."""
    await asyncio.sleep(1)
    return f"Echo: {message}"


# TODO: This is a mock function of sending response to the given user
async def send_response(user_id: str, response: str):
    """Send the generated response to the user (mock function)."""
    logging.info(f"[SEND] Responding to user {user_id}: {response}")
    return True


async def process_message():
    """Background worker that listens for new messages and processes them."""
    logging.info("Relay worker started...")
    while True:
        data = await async_redis.blpop("message_queue", timeout=0)
        if data:
            _, value = data
            user_id, message = value.split("|||", 1)
            logging.info(f"Processing message from user {user_id}: {message}")

            response = await generate_response(message)

            await send_response(user_id, response)

            await async_redis.rpush(f"user:{user_id}:responses", response)
            logging.info(f"Response generated and saved for user {user_id}: {response}")

        await asyncio.sleep(1)
        if asyncio.current_task().cancelled():
            break


###########################################################
#                          Score                          #
###########################################################


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
