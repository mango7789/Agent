import json
import logging
import subprocess
from redis import Redis
from .params import (
    REDIS_HOST,
    REDIS_POST,
    SCRAPER_LOG_DIR,
    SCRAPER_SCRIPT,
    SCRAPER_RUNNING_TASKS_KEY,
)
from .utils import get_curr_str_time
from .database import MongoDBDatabase

nsync_redis = Redis(host=REDIS_HOST, port=REDIS_POST, db=0, decode_responses=True)

def run_scraper(task_id: str):
    """Run the scraper subprocess."""
    TASK_QUERY = {"task_id": task_id}
    mongo_db = MongoDBDatabase()
    mongo_db.create_connection()

    nsync_redis.set(task_id, "Scraping")
    mongo_db.update_data("task", TASK_QUERY, {"status": "Scraping"})
    param_input = mongo_db.select_data("task", TASK_QUERY)[0]

    try:
        # Stream the output to log
        log_file = f"{SCRAPER_LOG_DIR}/{task_id}.log"
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                f"python {SCRAPER_SCRIPT} {param_input}",
                shell=True,
                stdout=log,
                stderr=subprocess.PIPE,
            )
        process.wait()

        # Write output to database
        nsync_redis.set(task_id, "Committing")
        mongo_db.update_data("task", TASK_QUERY, {"status": "Committing"})

        with open(log_file, "r") as log:
            try:
                buffer = ""
                # Iterate through resume list
                for line in log:
                    buffer += line.strip()

                    try:
                        record = json.loads(buffer)
                        record["created_at"] = get_curr_str_time()
                        mongo_db.insert_data("resume", record)
                        buffer = ""
                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                nsync_redis.set(task_id, f"Failed: {str(e)}")
                mongo_db.update_data("task", TASK_QUERY, {"status": "FormatError"})

        nsync_redis.set(task_id, "Finished")
        mongo_db.update_data("task", TASK_QUERY, {"status": "Finished"})

    except subprocess.CalledProcessError as e:
        nsync_redis.set(task_id, f"Failed: {str(e)}")
        mongo_db.update_data("task", TASK_QUERY, {"status": "ProcssError"})

    except Exception as e:
        nsync_redis.set(task_id, f"Failed: {str(e)}")
        mongo_db.update_data("task", TASK_QUERY, {"status": "UnknownError"})

    finally:
        nsync_redis.decr(SCRAPER_RUNNING_TASKS_KEY)
        mongo_db.close_connection()
