from typing import Final

# For scraper
SCRAPER_LOCK_KEY: Final = "scraper_task_lock"
SCRAPER_RUNNING_TASKS_KEY: Final = "running_scrapers"
SCRAPER_PENDING_TASKS_KEY: Final = "pending_scrapers"

MAX_RUNNING_TASKS: Final = 3
BATCH_SIZE: Final = 10

SCRAPER_SCRIPT: Final = "run_scraper.py"


# For message
