import os

import requests
from definitions import Phases, PreparationDialogs, PreparationDialogsTriggers
from celery import Celery
from virtual_coach_db.dbschema.models import Users
from virtual_coach_db.helper.helper import get_db_session

REDIS_URL = os.getenv('REDIS_URL')

app = Celery('celery_tasks', broker=REDIS_URL)

app.conf.beat_schedule = {
    'trigger_ask_foreseen_hrs': {
        'task': 'celery_tasks.trigger_ask_foreseen_hrs',
        'schedule': 3600.0, # every hour
        'args': (),
    },
}


@app.task
def dialog_completed(user_id, dialog_id):
    phase = get_current_phase(user_id)
    next_dialog = None
    if phase == Phases.PREPARATION:
        next_dialog = get_next_preparation_dialog(dialog_id)

    endpoint = f'http://rasa_server:5005/conversations/{user_id}/trigger_intent'
    headers = {'Content-Type': 'application/json'}
    params = {'output_channel': 'niceday_input_channel'}
    data = '{"name": "' + next_dialog[1] + '" }'
    requests.post(endpoint, headers=headers, params=params, data=data)


@app.task(bind=True)
def trigger_ask_foreseen_hrs(self):  # pylint: disable=unused-argument
    """Task to trigger RASA to set reminder for every user.
    """
    # TODO: add Celery or http error handling
    user_ids = get_user_ids()
    for user in user_ids:
        endpoint = f'http://rasa_server:5005/conversations/{user}/trigger_intent'
        headers = {'Content-Type': 'application/json'}
        params = {'output_channel': 'niceday_input_channel'}
        data = '{"name": "EXTERNAL_trigger_ask_foreseen_hrs"}'
        requests.post(endpoint, headers=headers, params=params, data=data)


def get_user_ids():
    """
    Get user ids of all existing users in the database
    TODO: Add filters, i.e. active users or in a specific phase of intervention.
    """
    session = get_db_session(db_url=os.getenv('DATABASE_URL'))
    users = session.query(Users).all()
    return [user.nicedayuid for user in users]

def get_current_phase(user_id):
    """
       Get the phase of the intervention of a user.

       """
    session = get_db_session(db_url=os.getenv('DATABASE_URL'))
    #  TODO: get phase from DB
    phase = Phases.PREPARATION
    return phase


def get_next_preparation_dialog(dialog_id):
    next_dialog = 0
    if dialog_id == PreparationDialogs.PROFILE_CREATION:
        next_dialog = [PreparationDialogs.MEDICATION_TALK, PreparationDialogsTriggers.MEDICATION_TALK.value]
    if dialog_id == PreparationDialogs.MEDICATION_TALK:
        next_dialog = [PreparationDialogs.COLD_TURKEY, PreparationDialogsTriggers.COLD_TURKEY.value]
    if dialog_id == PreparationDialogs.COLD_TURKEY:
        next_dialog = [PreparationDialogs.PLAN_QUIT_START_DATE, PreparationDialogsTriggers.PLAN_QUIT_START_DATE.value]
    if dialog_id == PreparationDialogs.PLAN_QUIT_START_DATE:
        next_dialog = [PreparationDialogs.FUTURE_SELF, PreparationDialogsTriggers.FUTURE_SELF.value]
    if dialog_id == PreparationDialogs.FUTURE_SELF:
        next_dialog = [PreparationDialogs.GOAL_SETTING, PreparationDialogsTriggers.GOAL_SETTING.value]

    return next_dialog
