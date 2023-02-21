import logging

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from dateutil.parser import isoparse

from utils import (
    is_intent_name,
    attributes_of,
    resolve_name_location,
    send_message,
    slots_of,
    get_source,
    resolve_complex_name_location,
    resolve_channel_location,
)
from constants import (
    AMAZON_CANCEL_INTENT,
    AMAZON_STOP_INTENT,
    PROVIDE_MESSAGE_INTENT,
    SESSION_LAST_MESSAGE_READ,
    SESSION_PROMPT,
    SLOT_LOCATION,
    SLOT_MESSAGE,
    SLOT_PROMPT,
    SLOT_TELL_MESSAGE,
    SLOT_COMPLEX_LOCATION,
    SESSION_GOAL,
    SEND_MESSAGE_GOAL,
    SESSION_LAST_HANDLER,
    SESSION_LAST_REQUEST,
    LAST_REQUEST_LOCATION,
    SESSION_LOCATION,
    LAST_REQUEST_MESSAGE,
    LAST_REQUEST_CONFIRM,
    SESSION_MESSAGE,
)
import open_ai_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SendMessageIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageIntentHandler'

    def can_handle(self, handler_input):
        return is_intent_name("SendMessageIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = attributes_of(handler_input)
        location = slots_of(handler_input)[SLOT_LOCATION].value
        tellMessage = slots_of(handler_input)[SLOT_TELL_MESSAGE].value
        complexLocation = slots_of(handler_input)[SLOT_COMPLEX_LOCATION].value
        session_attr[SESSION_GOAL] = SEND_MESSAGE_GOAL
        speak_output = f"Something went wrong and I didn't get overwritten. {slots_of(handler_input)}"
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = SendMessageIntentHandler.LAST_HANDLER_VALUE
        if location == None and tellMessage == None and complexLocation == None:
            session_attr[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION
            speak_output = "Great! Where would you like to send a message?"
        elif location != None and tellMessage == None and complexLocation == None:
            member, _ = resolve_name_location(location)
            member_name = member["real_name"]
            session_attr[SESSION_LOCATION] = member
            session_attr[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE
            speak_output = f"Alright! What would you like to say to { member_name }?"
        elif location == None and tellMessage != None and complexLocation == None:
            words = tellMessage.split(' ')
            location_name = words[0]
            member, _ = resolve_name_location(location_name)
            message = ' '.join(words[1:])
            speak_output = message_confirmation_string(member, message)
            attributes_of(handler_input)[SESSION_LOCATION] = member
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_CONFIRM
            attributes_of(handler_input)[SESSION_MESSAGE] = message
        elif location == None and tellMessage == None and complexLocation != None:
            words = complexLocation.split(' ')
            location = get_source(resolve_complex_name_location, resolve_channel_location, words)
            channel_name = location["name"]
            attributes_of(handler_input)[SESSION_LOCATION] = location
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE
            speak_output = f"Alright! What would you like to send to the {channel_name} channel?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SendMessageLocationIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageLocationIntentHandler'

    def last_request_was_location(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input) 
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_LOCATION
            and attributes_of(handler_input)[SESSION_GOAL] == SEND_MESSAGE_GOAL
        )


    def can_handle(self, handler_input):
        return self.last_request_was_location(handler_input) and is_intent_name("ProvideLocationIntent")(handler_input)

    def handle(self, handler_input):
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = SendMessageLocationIntentHandler.LAST_HANDLER_VALUE
        location = slots_of(handler_input)[SLOT_LOCATION].value
        member, _ = resolve_name_location(location)
        attributes_of(handler_input)[SESSION_LOCATION] = member
        if SESSION_GOAL not in attributes_of(handler_input):
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE
            speak_output = f"What would you like to say to {location}?"
        else:
            message = attributes_of(handler_input)[SESSION_MESSAGE]
            speak_output = message_confirmation_string(member, message)
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_CONFIRM

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def message_confirmation_string(member, message):
    name = None
    if "is_channel" in member and member["is_channel"]:
        name = member["name"]
    else:
        name = member["real_name"]
    return f"This is your message to { name }: {message} ... should I send it?"

class SendMessageMessageHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageMessageHandler'

    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input)
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_MESSAGE
            and is_intent_name(PROVIDE_MESSAGE_INTENT)(handler_input)
        )

    def handle(self, handler_input):
        message = slots_of(handler_input)[SLOT_MESSAGE].value
        member = attributes_of(handler_input)[SESSION_LOCATION]
        speak_output = message_confirmation_string(member, message)

        attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_CONFIRM
        attributes_of(handler_input)[SESSION_MESSAGE] = message
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = SendMessageMessageHandler.LAST_HANDLER_VALUE
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SendMessageIntentCatcher(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input)
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_MESSAGE
            and not is_intent_name(PROVIDE_MESSAGE_INTENT)(handler_input)
            and not is_intent_name(AMAZON_CANCEL_INTENT)(handler_input)
            and not is_intent_name(AMAZON_STOP_INTENT)(handler_input))

    def handle(self, handler_input):
        example = "I'm on my way"
        speak_output = f"I'm not sure where your message started. If your message is \"{example}\", say something like \"tell him '{example}'\""

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ConfirmMessageYesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input)
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_CONFIRM
            and is_intent_name("AMAZON.YesIntent")(handler_input)
        )

    def handle(self, handler_input):
        message = attributes_of(handler_input)[SESSION_MESSAGE]
        member = attributes_of(handler_input)[SESSION_LOCATION]

        response = send_message(member['id'], message)
        logger.info(f"Message sent: {response}")

        speak_output = f"Alright! Your message is sent! {message}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class ConfirmMessageNoIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'ConfirmMessageNoIntentHandler'
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input)
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_CONFIRM
            and is_intent_name("AMAZON.NoIntent")(handler_input)
        )

    def handle(self, handler_input):
        attributes_of(handler_input)[SESSION_MESSAGE] = None
        last_handler = attributes_of(handler_input)[SESSION_LAST_HANDLER]

        response = None
        if last_handler == SendMessageIntentHandler.LAST_HANDLER_VALUE:
            attributes_of(handler_input)[SESSION_LOCATION] = None
            speak_output = "Okay. I won't send it."
            response = (
                handler_input.response_builder
                .speak(speak_output)
                .response
            )
        else:
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE
            speak_output = f"Okay. What would you like your message to be?"
            response = (
                handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
            )
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = ConfirmMessageNoIntentHandler.LAST_HANDLER_VALUE
        return response

def wrap_draft(draft):
    return f"Here's your message: \"{draft}\"\nWho should I send it to?"

class DraftMessageIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DraftMessageIntent")(handler_input)
    
    def handle(self, handler_input):
        attributes_of(handler_input)[SESSION_GOAL] = SEND_MESSAGE_GOAL
        prompt = slots_of(handler_input)[SLOT_PROMPT]
        attributes_of(handler_input)[SESSION_PROMPT] = prompt

        draft = open_ai_client.draft_message(prompt)
        attributes_of(handler_input)[SESSION_MESSAGE] = draft

        speak_output = wrap_draft(draft)
        attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class DraftQuestionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DraftQuestionIntent")(handler_input)
    
    def handle(self, handler_input):
        attributes_of(handler_input)[SESSION_GOAL] = SEND_MESSAGE_GOAL
        prompt = slots_of(handler_input)[SLOT_PROMPT]
        attributes_of(handler_input)[SESSION_PROMPT] = prompt

        draft = open_ai_client.draft_question(prompt)
        attributes_of(handler_input)[SESSION_MESSAGE] = draft

        speak_output = wrap_draft(draft)
        attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class DraftReplyIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info("checking if DraftReplyIntentHandler can respond...")
        return (
            # SESSION_LAST_MESSAGE_READ in attributes_of(handler_input)
            is_intent_name("DraftReplyIntent")(handler_input)
        )
    
    def handle(self, handler_input):
        logger.info("Drafting Reply...")
        attributes_of(handler_input)[SESSION_GOAL] = SEND_MESSAGE_GOAL
        prompt = attributes_of(handler_input)[SESSION_LAST_MESSAGE_READ]

        draft = open_ai_client.draft_reply(prompt)
        attributes_of(handler_input)[SESSION_MESSAGE] = draft

        speak_output = wrap_draft(draft)

        attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION
        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )
