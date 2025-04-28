import json
import subprocess
from redis import Redis
from .database import MySQLDatabase
from .params import *

nsync_redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
mysql_db = MySQLDatabase()


def run_scraper(param1: str, param2: str, job_id: str):
    """Run the scraper subprocess."""
    nsync_redis.set(job_id, "Scraping")
    try:
        # Stream the output to log
        log_file = f"{SCRAPER_LOG_DIR}/{job_id}.log"
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                f"python {SCRAPER_SCRIPT} {param1} {param2}",
                shell=True,
                stdout=log,
                stderr=subprocess.PIPE,
            )
        process.wait()

        nsync_redis.set(job_id, "Committing")
        # NOTE: The log file is processed after the termination of scraper process
        with open(log_file, "r") as log:
            batch = []
            for line in log:
                try:
                    record = json.loads(line)
                    batch.append(record)

                    if len(batch) >= BATCH_SIZE:
                        mysql_db.insert_data_batch(batch)
                        batch.clear()

                except json.JSONDecodeError as e:
                    pass

            if batch:
                mysql_db.insert_data_batch(batch)

        nsync_redis.set(job_id, "Finished")

    except subprocess.CalledProcessError as e:
        nsync_redis.set(job_id, f"Failed: {str(e)}")

    except Exception as e:
        nsync_redis.set(job_id, f"Failed: {str(e)}")

    finally:
        nsync_redis.decr(SCRAPER_RUNNING_TASKS_KEY)
