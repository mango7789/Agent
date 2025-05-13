import json
import shlex
import subprocess
from bson import ObjectId
from redis import Redis
from .params import (
    REDIS_HOST,
    REDIS_POST,
    TABLE,
    SCRAPER_DIR,
    SCRAPER_LOG_DIR,
    SCRAPER_RUNNING_TASKS_KEY,
)
from .utils import get_curr_str_time
from .database import MongoDBDatabase

nsync_redis = Redis(host=REDIS_HOST, port=REDIS_POST, db=0, decode_responses=True)


def run_scraper(task_id: str):
    """Run the scraper subprocess."""
    try:
        TASK_QUERY = {"task_id": task_id}
        mongo_db = MongoDBDatabase()
        mongo_db.create_connection()

        nsync_redis.set(task_id, "Scraping")
        mongo_db.update_data(TABLE.TASK.value, TASK_QUERY, {"status": "Scraping"})
        param_input = mongo_db.select_data(TABLE.TASK.value, TASK_QUERY)[0]
        param_input = {
            k: v for k, v in param_input.items() if not isinstance(v, ObjectId)
        }

        param_input = json.dumps(param_input)

        # Stream the output to log
        log_file = f"{SCRAPER_LOG_DIR}/{task_id}.log"
        process = subprocess.run(
            f"python main.py {shlex.quote(param_input)}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=SCRAPER_DIR,
        )
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                process.args,
                output=process.stdout,
                stderr=process.stderr,
            )

        with open(log_file, "w") as log:
            log.write(process.stdout)

        # Write output to database
        nsync_redis.set(task_id, "Committing")
        mongo_db.update_data(TABLE.TASK.value, TASK_QUERY, {"status": "Committing"})

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
                mongo_db.update_data(
                    TABLE.TASK.value, TASK_QUERY, {"status": "FormatError"}
                )

        nsync_redis.set(task_id, "Finished")
        mongo_db.update_data(TABLE.TASK.value, TASK_QUERY, {"status": "Finished"})

    except subprocess.CalledProcessError as e:
        nsync_redis.set(task_id, f"Failed: {str(e)}")
        mongo_db.update_data(TABLE.TASK.value, TASK_QUERY, {"status": "ProcessError"})

    except Exception as e:
        nsync_redis.set(task_id, f"Failed: {str(e)}")
        mongo_db.update_data(TABLE.TASK.value, TASK_QUERY, {"status": "UnknownError"})

    finally:
        nsync_redis.decr(SCRAPER_RUNNING_TASKS_KEY)
        mongo_db.close_connection()


if __name__ == "__main__":
    with open("./template/task.json", "r") as f:
        param_input = json.load(f)
        param_input = json.dumps(param_input, ensure_ascii=False)

    process = subprocess.run(
        f"python main.py {shlex.quote(param_input)}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=SCRAPER_DIR,
    )

    print("=== STDOUT ===")
    print(process.stdout)

    print("=== STDERR ===")
    print(process.stderr)

    print("=== RETURN CODE ===")
    print(process.returncode)
