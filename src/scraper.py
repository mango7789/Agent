import json
import logging
import subprocess
from redis import Redis
from .database import MySQLDatabase
from .params import BATCH_SIZE, SCRAPER_RUNNING_TASKS_KEY, SCRAPER_SCRIPT

nsync_redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
mysql_db = MySQLDatabase()


def run_scraper(param1: str, param2: str, job_id: str):
    """Run the scraper subprocess."""
    nsync_redis.set(job_id, "Running")
    try:
        # Stream the output to log
        log_file = f"./logs/scraper/{job_id}.log"
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                f"python {SCRAPER_SCRIPT} {param1} {param2}",
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

    except Exception as e:
        nsync_redis.set(job_id, f"Failed: {str(e)}")
        logging.error(f"[{job_id}]: Unexpected error occurred: {e}")

    finally:
        nsync_redis.decr(SCRAPER_RUNNING_TASKS_KEY)
