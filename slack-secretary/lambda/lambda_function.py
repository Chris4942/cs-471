# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import json
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PROVIDE_MESSAGE_INTENT = 'ProvideMessageIntent'
AMAZON_CANCEL_INTENT = "AMAZON.CancelIntent"
AMAZON_STOP_INTENT = "AMAZON.StopIntent"

SLOT_LOCATION = 'location'
SLOT_MESSAGE = 'message'
SLOT_TELL_MESSAGE = 'tellMessage'

SESSION_LOCATION = 'location'
SESSION_LAST_REQUEST = 'lastRequest'
SESSION_GOAL = 'goal'
SESSION_MESSAGE = 'message'
SESSION_LAST_HANDLER = 'lastHandler'

MESSAGE_REQUEST = 'messageRequest'
SEND_MESSAGE_GOAL = 'sendMessage'
LAST_REQUEST_LOCATION = 'location'
LAST_REQUEST_MESSAGE = 'message'
LAST_REQUEST_CONFIRM = 'confirm'

def slots_of(handler_input):
    return handler_input.request_envelope.request.intent.slots

def attributes_of(handler_input):
    return handler_input.attributes_manager.session_attributes

def is_intent_name(intent_name):
    return ask_utils.is_intent_name(intent_name)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can ask me to send a message to someone for you. That's all for now."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Hello World!"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SendMessageIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageIntentHandler'

    def can_handle(self, handler_input):
        return is_intent_name("SendMessageIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = attributes_of(handler_input)
        location = slots_of(handler_input)[SLOT_LOCATION].value
        tellMessage = slots_of(handler_input)[SLOT_TELL_MESSAGE].value
        session_attr[SESSION_GOAL] = SEND_MESSAGE_GOAL
        speak_output = f"Something went wrong and I didn't get overwritten. {traceback.print_stack()}"
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = SendMessageIntentHandler.LAST_HANDLER_VALUE
        if location == None and tellMessage == None:
            session_attr[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION
            speak_output = "Great! Where would you like to send a message?"
        elif location != None and tellMessage == None:
            session_attr[SESSION_LOCATION] = location
            session_attr[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE
            speak_output = f"Alright! What would you like to say to {location}?"
        elif location == None and tellMessage != None:
            words = tellMessage.split(' ')
            # TODO do something cool with the api here, but for now we're doing this dumb thing instead
            location = words[0]
            message = ' '.join(words[1:])
            speak_output = message_confirmation_string(location, message)
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_CONFIRM
            attributes_of(handler_input)[SESSION_MESSAGE] = message
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SendMessageLocationIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageLocationIntentHandler'

    def last_request_was_location(self, handler_input):
        return attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_LOCATION


    def can_handle(self, handler_input):
        return self.last_request_was_location(handler_input) and is_intent_name("ProvideLocationIntent")(handler_input)

    def handle(self, handler_input):
        location = slots_of(handler_input)[SLOT_LOCATION].value
        attributes_of(handler_input)[SESSION_LOCATION] = location
        speak_output = f"What would you like to say to {location}?"
        attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_MESSAGE

        attributes_of(handler_input)[SESSION_LAST_HANDLER] = SendMessageLocationIntentHandler.LAST_HANDLER_VALUE
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def message_confirmation_string(location, message):
    return f"This is your message to {location}: {message} ... should I send it?"

class SendMessageMessageHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'SendMessageMessageHandler'

    def can_handle(self, handler_input):
        return attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_MESSAGE and is_intent_name(PROVIDE_MESSAGE_INTENT)(handler_input)

    def handle(self, handler_input):
        message = slots_of(handler_input)[SLOT_MESSAGE].value
        location = attributes_of(handler_input)[SESSION_LOCATION]
        speak_output = message_confirmation_string(location, message)

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
        return (attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_MESSAGE
            and not is_intent_name(PROVIDE_MESSAGE_INTENT)(handler_input)
            and not is_intent_name(AMAZON_CANCEL_INTENT)(handler_input)
            and not is_intent_name(AMAZON_STOP_INTENT)(handler_input))

    def handle(self, handler_input):
        example = "I'm on my way"
        speak_output = f"I'm not sure where you message started. If your message is \"{example}\", say something like \"tell him '{example}'\""

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ConfirmMessageYesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_CONFIRM and is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        # TODO actually send it
        message = attributes_of(handler_input)[SESSION_MESSAGE]

        speak_output = f"Alright! Your message is sent! {message}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class ConfirmMessageNoIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = 'ConfirmMessageNoIntentHandler'
    def can_handle(self, handler_input):
        return attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_CONFIRM and is_intent_name("AMAZON.NoIntent")(handler_input)

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

class GetSessionIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GetSessionData")(handler_input)

    def handle(self, handler_input):
        session_attr = attributes_of(handler_input)
        speak_output = json.dumps(session_attr)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (is_intent_name(AMAZON_CANCEL_INTENT)(handler_input) or
                is_intent_name(AMAZON_STOP_INTENT)(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # TODO Any cleanup logic goes here.
        return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = f"Sorry, I had trouble doing what you asked. Please try again.\n{exception}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SendMessageIntentHandler())
sb.add_request_handler(GetSessionIntent())
sb.add_request_handler(SendMessageLocationIntentHandler())
sb.add_request_handler(SendMessageMessageHandler())
sb.add_request_handler(SendMessageIntentCatcher())
sb.add_request_handler(ConfirmMessageNoIntentHandler())
sb.add_request_handler(ConfirmMessageYesIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()