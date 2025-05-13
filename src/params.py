from typing import Final

###########################################################
#                    Infrastructure                       #
###########################################################
APP_HOST: Final = "127.0.0.1"
APP_PORT: Final = 8000

REDIS_HOST: Final = "localhost"
REDIS_POST: Final = 6379

MONGO_HOST: Final = "localhost"
MONGO_POST: Final = 27017


###########################################################
#                         App                             #
###########################################################
RQ_LOG_DIR: Final = "logs/rq"
APP_LOG_DIR: Final = "logs/app"


###########################################################
#                       Scraper                           #
###########################################################
# Redis keys for tracking scraper tasks
SCRAPER_QUEUE_KEY: Final = "scraper_queue"
SCRAPER_RUNNING_TASKS_KEY: Final = "running_scrapers"
SCRAPER_PENDING_TASKS_KEY: Final = "pending_scrapers"

# Scraper parameters
MAX_RUNNING_TASKS: Final = 3

# Paths for scraper scripts and logs
SCRAPER_SCRIPT: Final = "scraper/main.py"
SCRAPER_LOG_DIR: Final = "logs/scraper"


###########################################################
#                     Message Relay                       #
###########################################################
# Redis keys for tracking messages
MESSAGE_QUEUE_KEY: Final = "message_queue"
