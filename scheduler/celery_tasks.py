import logging
import os
import requests
from celery import Celery
from datetime import datetime, timedelta
from state_machine.state_machine import StateMachine, EventEnum, Event
from state_machine.const import REDIS_URL, TIMEZONE
from state_machine.controller import OnboardingState
from virtual_coach_db.helper.definitions import Components

app = Celery('celery_tasks', broker=REDIS_URL)

app.conf.enable_utc = True
app.conf.timezone = TIMEZONE

TEST_USER = int(os.getenv('TEST_USER_ID'))

state_machines = [{'machine': StateMachine(OnboardingState(TEST_USER)), 'id': TEST_USER}]


# state_machines = []


@app.task
def create_new_user(user_id: int):
    # this is a placeholder for the creation of a new user. At the moment we initialize
    # just one fsm with a test user
    global state_machines

    state_machines.append({'machine': StateMachine(OnboardingState(user_id)), 'id': user_id})


@app.task
def start_user_intervention(user_id: int):
    # run the first state
    user_fsm = next(item for item in state_machines if item['id'] == user_id)['machine']
    user_fsm.state.run()


@app.task(bind=True)
def user_trigger_dialog(self,
                        user_id: int,
                        triggered_dialog: Components):  # pylint: disable=unused-argument
    send_fsm_event(user_id=user_id, event=Event(EventEnum.USER_TRIGGER, triggered_dialog))


@app.task(bind=True)
def notify_new_day(self, current_date: datetime.date):  # pylint: disable=unused-argument
    [send_fsm_event(user_id=item['id'], event=Event(EventEnum.NEW_DAY, current_date)) for item in state_machines]
    # schedule the task for tomorrow
    tomorrow = datetime.today() + timedelta(days=1)
    notify_new_day.apply_async(args=[tomorrow], eta=tomorrow)


# TODO: implement a cleaner way to start the day counter
notify_new_day.apply_async(args=[datetime.today()])


@app.task(bind=True)
def intervention_component_completed(self,
                                     user_id: int,
                                     completed_dialog: Components):  # pylint: disable=unused-argument

    logging.info('Celery received a dialog completion')
    send_fsm_event(user_id=user_id, event=Event(EventEnum.DIALOG_COMPLETED, completed_dialog))


@app.task
def reschedule_dialog(user_id: int, intervention_component_name: str, new_date: datetime):

    logging.info('Celery received a dialog rescheduling')
    send_fsm_event(user_id=user_id,
                   event=Event(EventEnum.DIALOG_RESCHEDULED, (intervention_component_name, new_date)))


@app.task(bind=True)
def trigger_intervention_component(self, user_id, trigger):  # pylint: disable=unused-argument
    endpoint = f'http://rasa_server:5005/conversations/{user_id}/trigger_intent'
    headers = {'Content-Type': 'application/json'}
    params = {'output_channel': 'niceday_trigger_input_channel'}
    data = '{"name": "' + trigger + '" }'
    requests.post(endpoint, headers=headers, params=params, data=data, timeout=60)


def send_fsm_event(user_id: int, event: Event):
    # get the user state machine
    user_fsm = next(item for item in state_machines if item['id'] == user_id)['machine']
    user_fsm.on_event(event)
