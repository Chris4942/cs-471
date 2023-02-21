# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging

from constants import INFO_MESSAGE

from read_messages import ReadMessageIntentHandler, ReadMessageLocationIntentHandler, ReadMessageProvideNumberIntentHandler, ReadMessageProvideTimeBoundingIntentHandler

from send_message import ConfirmMessageNoIntentHandler, ConfirmMessageYesIntentHandler, SendMessageIntentCatcher, SendMessageIntentHandler, SendMessageLocationIntentHandler, SendMessageMessageHandler

from utils import attributes_of, is_intent_name
import ask_sdk_core.utils as ask_utils
import re

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import json


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO the token is below is for an inconsequential slack workspace. This would need to be done differently if this were ever used in production


time_reg_ex = re.compile("\d\d:\d\d")

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can ask me to send a message to someone or to a channel for you, or you can ask me to read messages from a channel. What would you like me to do?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

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
        speak_output = INFO_MESSAGE

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
        speak_out = "I didn't catch that. "
        session = attributes_of(handler_input)
        if SESSION_GOAL in session:
            if session[SESSION_GOAL] == SEND_MESSAGE_GOAL:
                speak_out += "I think you want to send a message. "
                if SESSION_LAST_REQUEST in session:
                    if session[SESSION_LAST_REQUEST] == SESSION_LOCATION:
                        speak_out += "Where would you like to send it?"
                    elif session[SESSION_LAST_REQUEST] == LAST_REQUEST_MESSAGE:
                        speak_out += "What would you like to say?"
                    elif session[SESSION_LAST_REQUEST] == LAST_REQUEST_CONFIRM:
                        message = session[SESSION_MESSAGE]
                        speak_out += f"This is what I have: {message}... Would you like to send it?"
                else:
                    speak_out += "Where would you like to send it?"
            elif session[SESSION_GOAL] == READ_MESSAGE_GOAL:
                speak_out += "I think you want me to read message. "
                if SESSION_LAST_REQUEST[SESSION_LAST_REQUEST] == LAST_REQUEST_LOCATION:
                    speak_out += " What channel do you want me to read messages from?"
                if SESSION_LAST_REQUEST[SESSION_LAST_REQUEST] == LAST_REQUEST_NUMBER:
                    num_items = len(session[SESSION_ITEMS])
                    channel = session[SESSION_LOCATION]
                    speak_out += f" There are {num_items} messages in {channel}. How many would you like me to read?"
        else:
            speak_out += INFO_MESSAGE


        return handler_input.response_builder.speak(speak_out).ask(speak_out).response

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

        speak_output = f"Sorry, I had trouble doing what you asked. Please try again.\n{exception}, {json.dumps(attributes_of(handler_input))}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ChannelNotFoundExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return isinstance(exception, ChannelNotFoundException)
    
    def handle(self, handler_input, exception):
        speak_output = f"Sorry, I wasn't able to find that channel. I am not able to read messages recieved directly from a user. See Project Write Up Limitations for more details."

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
sb.add_request_handler(ReadMessageIntentHandler())
sb.add_request_handler(ReadMessageProvideNumberIntentHandler())
sb.add_request_handler(ReadMessageProvideTimeBoundingIntentHandler())
sb.add_request_handler(ReadMessageLocationIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(ChannelNotFoundExceptionHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()