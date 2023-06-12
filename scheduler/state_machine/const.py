import os
from dateutil import tz

# maximum duration of the dialog in seconds
MAXIMUM_DIALOG_DURATION = 90*60

# time interval in seconds for checking for new connection requests
INVITES_CHECK_INTERVAL = 10*60

# PA groups
LOW_PA_GROUP = 1
HIGH_PA_GROUP = 2

# duration in weeks
EXECUTION_DURATION_WEEKS = 12

# intervention times (days)
ACTIVITY_C2_9_DAY_TRIGGER = 7
FUTURE_SELF_INTRO = 8
GOAL_SETTING = 9
TRACKING_DURATION = 10
PREPARATION_GA = 14
MAX_PREPARATION_DURATION = 21
EXECUTION_DURATION = EXECUTION_DURATION_WEEKS * 7  # 12 weeks
#

REDIS_URL = os.getenv('REDIS_URL')
DATABASE_URL = os.getenv('DATABASE_URL')
NICEDAY_API_ENDPOINT = os.getenv('NICEDAY_API_ENDPOINT')
TRIGGER_COMPONENT = 'celery_tasks.trigger_intervention_component'
SCHEDULE_TRIGGER_COMPONENT = 'celery_tasks.trigger_scheduled_intervention_component'
TRIGGER_MENU = 'celery_tasks.trigger_menu'
TIMEZONE = tz.gettz("Europe/Amsterdam")

# dialog states definitions
NOT_RUNNING = 0
RUNNING = 1
EXPIRED = 2
