# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import re

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
from datetime import date, datetime
from dateutil.parser import isoparse

import json
import traceback

from requests import get, post

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO the token is below is for an inconsequential slack workspace. This would need to be done differently if this were ever used in production
HEADERS = {"Authorization": "Bearer xoxb-4753428053280-4742434306049-9soWlaebmTXMm2XkZRbfQLJL"}

INFO_MESSAGE = "I can send a message or read messages to you. What would you like me to do?"

PROVIDE_MESSAGE_INTENT = 'ProvideMessageIntent'
AMAZON_CANCEL_INTENT = "AMAZON.CancelIntent"
AMAZON_STOP_INTENT = "AMAZON.StopIntent"
PROVIDE_NUMBER_INTENT = 'ProvideNumberIntent'
ALL_INTENT = 'AllIntent'

MAX_MESSAGE_READOUT = 3

SLOT_LOCATION = 'location'
SLOT_MESSAGE = 'message'
SLOT_TELL_MESSAGE = 'tellMessage'
SLOT_COMPLEX_LOCATION = 'complexLocation'
SLOT_NUMBER = 'number'
SLOT_START_TIME = 'startTime'
SLOT_END_TIME = 'endTime'
SLOT_START_DATE = 'startDate'
SLOT_END_DATE = 'endDate'

SESSION_LOCATION = 'location'
SESSION_LAST_REQUEST = 'lastRequest'
SESSION_GOAL = 'goal'
SESSION_MESSAGE = 'message'
SESSION_LAST_HANDLER = 'lastHandler'
SESSION_ITEMS = 'items'
SESSION_CONVERSATION_ID = 'sessionConversationId'

MESSAGE_REQUEST = 'messageRequest'
SEND_MESSAGE_GOAL = 'sendMessage'
READ_MESSAGE_GOAL = 'readMessage'
LAST_REQUEST_LOCATION = 'location'
LAST_REQUEST_MESSAGE = 'message'
LAST_REQUEST_CONFIRM = 'confirm'
LAST_REQUEST_NUMBER = 'number'

user_cache = {}
user_cache_populated = False

def get_users():
    global user_cache_populated
    if user_cache_populated:
        return user_cache
    else:
        json_body = get('https://slack.com/api/users.list', headers=HEADERS).json()
        members = json_body["members"]
        for user in members:
            user_cache[user['id']] = user
        user_cache_populated = True
        return get_users()

def get_user(id):
    if id not in user_cache:
        get_users()
    return user_cache[id]

def slots_of(handler_input):
    return handler_input.request_envelope.request.intent.slots

def slot_details(handler_input):
    return handler_input.request_envelope.request.intent

def attributes_of(handler_input):
    return handler_input.attributes_manager.session_attributes

def is_intent_name(intent_name):
    return ask_utils.is_intent_name(intent_name)

def find_best_match(list, target, matching_fun):
    best_match = None
    best_match_score = 0.0
    for item in list:
        score = matching_fun(target, item)
        logger.info(f"{score}, {item}, {target}")
        if score > best_match_score:
            best_match = item
            best_match_score = score
    return best_match, best_match_score

def resolve_name_location(location_name):
    members = get_users().values()
    def rate_match(current_location_name, member):
        current_location_name_lower = current_location_name.lower()
        real_name = member["real_name"].lower()
        logger.info(f"names: {current_location_name}, {real_name}. Conditions: {current_location_name.lower()}, {real_name in current_location_name_lower}, {current_location_name_lower in real_name}")
        if current_location_name_lower == real_name:
            return 1.0
        if current_location_name_lower in real_name or real_name in current_location_name_lower:
            logger.info("Reached the code where we return a 0.9")
            return 0.9
        return 0.0
    return find_best_match(members, location_name, rate_match)

def resolve_complex_name_location(words):
    members = get_users().values()
    def rate_match(words, member):
        total_matches = 0
        for word in words:
            if word.lower() in member["real_name"].lower() or member["real_name"].lower() in word.lower():
                total_matches += 1
        return total_matches
    return find_best_match(members, words, rate_match)

def resolve_simple_channel_location(name):
    channels = get('https://slack.com/api/conversations.list', headers=HEADERS).json()['channels']
    def rate_match(current_location_name, member):
        current_location_name_lower = current_location_name.lower()
        member_name = member["name"].lower()
        if current_location_name_lower == member_name:
            return 1.0
        if current_location_name_lower in member_name or member_name in current_location_name_lower:
            return 0.9
        return 0.0
    return find_best_match(channels, name, rate_match)

def resolve_channel_location(words):
    channels = get('https://slack.com/api/conversations.list', headers=HEADERS).json()['channels']
    def rate_match(words, channel):
        total_matches = 0
        for word in words:
            if word.lower() in channel["name"].lower() or channel["name"].lower() in word.lower():
                total_matches += 1
        return total_matches
    return find_best_match(channels, words, rate_match)

def send_message(channel, message):
    return post("https://slack.com/api/chat.postMessage", data={
        "channel": channel,
        "text": message,
    }, headers=HEADERS).json()

class ChannelNotFoundException(Exception):
    def __init__(self, message):
        super(ChannelNotFoundException, self)
        self.message = message

def get_messages(conversation_id, start_time, end_time):
    url = f"https://slack.com/api/conversations.history?channel={conversation_id}"
    if start_time != None:
        url += f"&oldest={start_time}"
    if end_time != None:
        url += f"&latest={end_time}"
    logger.info(f"getting messages from url: {url}")
    json_body = get(url, headers=HEADERS).json()
    logger.info(f"messages response body: {json_body}")

    if 'error' in json_body and json_body['error'] == 'channel_not_found':
        raise ChannelNotFoundException(f"Unable to find channel with id {conversation_id}")
    
    return filter(
        lambda item: "subtype" not in item,
        json_body["messages"]
    )

time_literals = {
    "NI": "19:00",
    "MO": "07:00",
    "AF": "12:00",
    "EV": "05:00",
}

time_reg_ex = re.compile("\d\d:\d\d")

def convert_time_to_ms(date, time):
    if date == None and time == None:
        return None
    logger.info(f"convert_time_to_ms.time = {time}")
    time_string = '00:00' if time == None else time_literals[time] if time_reg_ex.match(time) else time
    date_string = date.today().isoformat() if date == None else date
    date_time_string = f"{date_string}T{time_string}"
    logger.info(f"converting date_time_string: {date_time_string}. today_string: {date_string}")
    timestamp = isoparse(date_time_string).timestamp()
    if timestamp > datetime.now().timestamp():
        timestamp -= (24 * 60 * 60)
    return timestamp

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
            location, _ = resolve_channel_location(words)
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

def get_source(name_resolver, channel_resolver, index):
    name, name_confidence = name_resolver(index)
    channel, channel_confidence = channel_resolver(index)
    return name if name_confidence > channel_confidence else channel

def coordinate_message_getting(source_string, start_date_time, end_date_time):
    words = source_string.split(' ')
    logger.info(f"words = {words}")
    source = None
    if len(words) == 1:
        source = get_source(resolve_name_location, resolve_simple_channel_location, source_string)
    elif len(words) > 1:
        source = get_source(resolve_complex_name_location, resolve_channel_location, words)
    messages = get_messages(source["id"], start_date_time, end_date_time)
    items = [message for message in map(lambda item: {
            'message': item["text"],
            'user_id': item['user']
        }, messages)]
    return items, source

class ReadMessageIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = "ReaddMessageIntentHandler"

    def can_handle(self, handler_input):
        return is_intent_name("ReadMessageIntent")(handler_input)

    
    def handle(self, handler_input):
        location = slots_of(handler_input)[SLOT_LOCATION].value
        number = slots_of(handler_input)[SLOT_NUMBER].value
        start_time = slots_of(handler_input)[SLOT_START_TIME].value
        end_time = slots_of(handler_input)[SLOT_END_TIME].value
        start_date = slots_of(handler_input)[SLOT_START_DATE].value
        end_date = slots_of(handler_input)[SLOT_END_DATE].value
        start_date_time = convert_time_to_ms(start_date, start_time)
        end_date_time = convert_time_to_ms(end_date, end_time)
        logger.info(f"{slot_details(handler_input)}")
        debug_data = f"location: {location}. number: {number}"
        speak_output = f"You've reach the ReadMessageIntent. ${debug_data}"
        source_string = location if location != None else None
        logger.info(f"source_string = {source_string}")
        attributes_of(handler_input)[SESSION_GOAL] = READ_MESSAGE_GOAL
        if source_string != None:
            items, source = coordinate_message_getting(source_string, start_date_time, end_date_time)
            speak_output = ""
            if len(items) > MAX_MESSAGE_READOUT:
                attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_NUMBER
                attributes_of(handler_input)[SESSION_ITEMS] = items
                attributes_of(handler_input)[SESSION_CONVERSATION_ID] = source['id']
                speak_output = f"I found {len(items)} messages. How many recent messages would you like me to read or what time range would you like to me to read messages in?"
            else:
                speak_output = compile_items_into_speak_output(items)
        else:
            speak_output = "What channel would you like me to read messages from?"
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_LOCATION
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = ReadMessageIntentHandler.LAST_HANDLER_VALUE
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ReadMessageLocationIntentHandler(AbstractRequestHandler):
    LAST_HANDLER_VALUE = "ReadMessageLocationIntentHandler"
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input) 
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_LOCATION
            and attributes_of(handler_input)[SESSION_GOAL] == READ_MESSAGE_GOAL
        )

    def handle(self, handler_input):
        location = slots_of(handler_input)[SLOT_LOCATION].value
        items, source = coordinate_message_getting(location, None, None)
        speak_output = "" 
        if len(items) > MAX_MESSAGE_READOUT:
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_NUMBER
            attributes_of(handler_input)[SESSION_ITEMS] = items
            attributes_of(handler_input)[SESSION_CONVERSATION_ID] = source['id']
            speak_output = f"I found {len(items)} messages. How many recent messages would you like me to read or what time range would you like to me to read messages in?"
        else:
            speak_output = compile_items_into_speak_output(items)
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = ReadMessageLocationIntentHandler.LAST_HANDLER_VALUE
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def compile_items_into_speak_output(items):
    speak_output = ""
    for item in reversed(items):
        user = get_user(item['user_id'])['real_name']
        speak_output = f"{speak_output} {user} said \"{item['message']}\"."
    return speak_output

class ReadMessageProvideNumberIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_NUMBER
            and (
                is_intent_name(PROVIDE_NUMBER_INTENT)(handler_input)
                or is_intent_name(ALL_INTENT)
            )
        )
    
    def handle(self, handler_input):
        items = attributes_of(handler_input)[SESSION_ITEMS]
        number = (int(slots_of(handler_input)[SLOT_NUMBER].value) if is_intent_name(PROVIDE_NUMBER_INTENT)(handler_input)
            else len(items) if is_intent_name(ALL_INTENT)
            else None
        )
        if number == None:
            raise Exception("I don't know how this happened, but I certainly didn't prepare for it")
        logger.info(f"number type: {type(number)}")
        logger.info(f"items: {items[len(items) - number:]}")
        items = items[len(items) - number:]
        speak_output = compile_items_into_speak_output(items)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ReadMessageProvideTimeBoundingIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_NUMBER
            and attributes_of(handler_input)[SESSION_LAST_HANDLER] == ReadMessageIntentHandler.LAST_HANDLER_VALUE
            and is_intent_name("ProvideTimeBoundingIntent")(handler_input)
        )

    def handle(self, handler_input):
        start_time = slots_of(handler_input)[SLOT_START_TIME].value
        end_time = slots_of(handler_input)[SLOT_END_TIME].value
        start_date = slots_of(handler_input)[SLOT_START_DATE].value
        end_date = slots_of(handler_input)[SLOT_END_DATE].value
        start_date_time = convert_time_to_ms(start_date, start_time)
        end_date_time = convert_time_to_ms(end_date, end_time)
        logger.info(f"start_time: {start_time}. end_time: {end_time}")
        conversation_id = attributes_of(handler_input)[SESSION_CONVERSATION_ID]
        messages = get_messages(conversation_id, start_date_time, end_date_time)
        items = [message for message in map(lambda item: {
                'message': item["text"],
                'user_id': item['user']
            }, messages)]

        speak_output=""
        if len(items) > MAX_MESSAGE_READOUT:
            attributes_of(handler_input)[SESSION_LAST_REQUEST] = LAST_REQUEST_NUMBER
            attributes_of(handler_input)[SESSION_LAST_HANDLER] = ReadMessageIntentHandler.LAST_HANDLER_VALUE
            attributes_of(handler_input)[SESSION_ITEMS] = items
            speak_output = f"I found {len(items)} messages. How many recent messages would you like me to read?"
        else:
            speak_output = compile_items_into_speak_output(items)
        
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