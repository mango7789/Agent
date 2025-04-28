from typing import Final

###########################################################
#                         App                             #
###########################################################
APP_LOG_DIR: Final = "logs/app"
RQ_LOG_FILE: Final = "logs/rq/worker.log"

###########################################################
#                       Scraper                           #
###########################################################
# Redis keys for tracking scraper tasks
SCRAPER_RUNNING_TASKS_KEY: Final = "running_scrapers"
SCRAPER_PENDING_TASKS_KEY: Final = "pending_scrapers"

# Scraper parameters
MAX_RUNNING_TASKS: Final = 3
BATCH_SIZE: Final = 10

# Paths for scraper scripts and logs
SCRAPER_SCRIPT: Final = "run_scraper.py"
SCRAPER_LOG_DIR: Final = "logs/scraper"


###########################################################
#                     Message Relay                       #
###########################################################
# Redis keys for tracking messages
MESSAGE_QUEUE_KEY = "message_queue"
