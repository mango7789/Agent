import uuid
import json
import asyncio
import logging
import subprocess
import uvicorn
from rq import Queue
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from fastapi import FastAPI

from utils.params import *
from utils.database import MySQLDatabase

app = FastAPI()

# Redis connections
nsync_redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
async_redis = AsyncRedis(host="localhost", port=6379, db=0, decode_responses=True)

# RQ Queue
scraper_queue = Queue(connection=nsync_redis)

# Logger setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database connection
mysql_db = MySQLDatabase()

###########################################################
#                   Initialization                        #
###########################################################

# TODO: Establish a session with the website


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks when the app starts."""
    asyncio.create_task(scraper_scheduler())
    asyncio.create_task(message_monitor())
    asyncio.create_task(process_message())


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down."""
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()


###########################################################
#                       Scraper                           #
###########################################################


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


def run_scraper(param1: str, param2: str, job_id: str):
    """Run the scraper subprocess."""
    nsync_redis.set(job_id, "Running")
    try:
        # Stream the output to log
        log_file = f"../logs/scraper/{job_id}.log"
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                f"python run_scraper.py {param1} {param2}",
                shell=True,
                stdout=log,
                stderr=subprocess.PIPE,
            )
        process.wait()

        # NOTE: The log file is processed after the termination of scraper process
        with open(log_file, "r") as log:
            batch = []
            for line in log:
                try:
                    record = json.loads(line)
                    batch.append(record)

                    if len(batch) >= BATCH_SIZE:
                        mysql_db.insert_data_batch(batch)
                        logging.info(
                            f"[{job_id}]: Inserted a batch of {BATCH_SIZE} records into the database."
                        )
                        batch.clear()

                except json.JSONDecodeError as e:
                    logging.error(f"[{job_id}]: Failed to decode line as JSON: {line}")

            if batch:
                mysql_db.insert_data_batch(batch)
                logging.info(
                    f"[{job_id}]: Inserted the last batch of {len(batch)} records into the database."
                )

        nsync_redis.set(job_id, "Finished")
        logging.info(f"[{job_id}]: Scraper task completed successfully.")

    except subprocess.CalledProcessError as e:
        nsync_redis.set(job_id, f"Failed: {str(e)}")
        logging.error(f"[{job_id}]: Scraper task failed: {e}")

    finally:
        nsync_redis.decr(SCRAPER_RUNNING_TASKS_KEY)


@app.post("/scraper")
async def scraper(param1: str, param2: str):
    """Submit a new scraper task."""
    job_id = str(uuid.uuid4())
    nsync_redis.set(job_id, "Pending")
    nsync_redis.rpush(SCRAPER_PENDING_TASKS_KEY, f"{param1},{param2},{job_id}")

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
    while True:
        user_id, message = await detect_new_message()
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
