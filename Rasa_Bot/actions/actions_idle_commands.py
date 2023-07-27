from celery import Celery
from rasa_sdk import Action
from .helper import dialog_to_be_completed,get_current_user_phase, get_dialog_completion_state
from virtual_coach_db.helper.definitions import Components
from .definitions import REDIS_URL, FsmStates

celery = Celery(broker=REDIS_URL)


class ActionTriggerRelapseDialog(Action):
    """Trigger the relapse the dialog"""

    def name(self):
        return "action_trigger_relapse_dialog"

    async def run(self, dispatcher, tracker, domain):
        user_id = tracker.current_state()['sender_id']

        phase = get_current_user_phase(user_id)

        # check if the dialog can be executed (the use is in the execution phase)
        if phase != FsmStates.EXECUTION_RUN:
            dispatcher.utter_message(response="utter_help_not_available")
        else:
            celery.send_task('celery_tasks.user_trigger_dialog',
                             (user_id, Components.RELAPSE_DIALOG))


class ActionTriggerFirstAidDialog(Action):
    """Trigger the first aid dialog"""

    def name(self):
        return "action_trigger_first_aid_dialog"

    async def run(self, dispatcher, tracker, domain):
        user_id = tracker.current_state()['sender_id']

        celery.send_task('celery_tasks.user_trigger_dialog', (user_id, Components.FIRST_AID_KIT))


class ActionTriggerExplainFirstAidVideoDialog(Action):
    """Trigger the first aid dialog explanation video"""

    def name(self):
        return "action_trigger_explanation_first_aid_video_dialog"

    async def run(self, dispatcher, tracker, domain):
        user_id = tracker.current_state()['sender_id']

        celery.send_task('celery_tasks.user_trigger_dialog', (user_id,
                                                              Components.FIRST_AID_KIT_VIDEO))


class ActionTriggerGeneralActivityDialog(Action):
    """Trigger the general activity dialog"""

    def name(self):
        return "action_trigger_general_activity_dialog"

    async def run(self, dispatcher, tracker, domain):
        user_id = tracker.current_state()['sender_id']

        celery.send_task('celery_tasks.user_trigger_dialog', (user_id, Components.GENERAL_ACTIVITY))


class ActionTriggerMedicineVideoDialog(Action):
    """Trigger the medicine video"""

    def name(self):
        return "action_trigger_video_medicine_dialog"

    async def run(self, dispatcher, tracker, domain):
        user_id = tracker.current_state()['sender_id']

        celery.send_task('celery_tasks.user_trigger_dialog', (user_id, Components.MEDICATION_TALK))


class ActionSelectMenu(Action):
    """Determines which list of commands has to be used"""

    def name(self):
        return "action_select_menu"

    async def run(self, dispatcher, tracker, domain):

        user_id = tracker.current_state()['sender_id']

        # is there a dialog to be completed
        complete_dialog = dialog_to_be_completed(user_id)
        # is the ehbo option to be shown (the explanatory video has been shown)
        show_ehbo = get_dialog_completion_state(user_id, Components.FIRST_AID_KIT_VIDEO)

        # the help command is shown just in the execution
        phase = get_current_user_phase(user_id)

        if phase != FsmStates.EXECUTION_RUN:
            show_help = False
        else:
            show_help = True

        # select the utterances

        # show the help command
        if show_help:
            dispatcher.utter_message(response="utter_central_mode_options_help")
        # show the ehbo command
        if show_ehbo:
            dispatcher.utter_message(response="utter_central_mode_options_ehbo")

        # show the exercise command
        dispatcher.utter_message(response="utter_central_mode_options_oefening")
        # show the medication video command
        dispatcher.utter_message(response="utter_central_mode_options_medicatie")
        # show the verder command
        if complete_dialog:
            dispatcher.utter_message(response="utter_central_mode_options_verder")
        # show the last general statement
        dispatcher.utter_message(response="utter_central_mode_options_outro")


class ActionTriggerUncompletedDialog(Action):
    """Trigger uncompleted dialog if there is one"""

    def name(self):
        return "action_trigger_uncompleted_dialog"

    async def run(self, dispatcher, tracker, domain):
        
        user_id = tracker.current_state()['sender_id']
        
        if dialog_to_be_completed(user_id):
            celery.send_task('celery_tasks.user_trigger_dialog',
                             (user_id, Components.CONTINUE_UNCOMPLETED_DIALOG))
        else:
            dispatcher.utter_message(response="utter_no_valid_uncompleted_dialog")
            dispatcher.utter_message(response="utter_central_mode_options_without_verder")
