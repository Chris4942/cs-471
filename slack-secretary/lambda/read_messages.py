

import logging

from constants import ALL_INTENT, LAST_REQUEST_LOCATION, LAST_REQUEST_NUMBER, MAX_MESSAGE_READOUT, PROVIDE_NUMBER_INTENT, READ_MESSAGE_GOAL, SESSION_CONVERSATION_ID, SESSION_GOAL, SESSION_ITEMS, SESSION_LAST_HANDLER, SESSION_LAST_MESSAGE_READ, SESSION_LAST_REQUEST, SLOT_END_DATE, SLOT_END_TIME, SLOT_LOCATION, SLOT_NUMBER, SLOT_START_DATE, SLOT_START_TIME


from ask_sdk_core.dispatch_components import AbstractRequestHandler
from utils import attributes_of, convert_time_to_ms, get_messages, get_source, get_user, is_intent_name, resolve_channel_location, resolve_complex_name_location, resolve_name_location, resolve_simple_channel_location, slot_details, slots_of


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
                speak_output = compile_items_into_speak_output(items, handler_input)
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
            and SESSION_GOAL in attributes_of(handler_input)
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
            speak_output = compile_items_into_speak_output(items, handler_input)
        attributes_of(handler_input)[SESSION_LAST_HANDLER] = ReadMessageLocationIntentHandler.LAST_HANDLER_VALUE
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def compile_items_into_speak_output(items, handler_input):
    speak_output = ""
    for item in reversed(items):
        user = get_user(item['user_id'])['real_name']
        speak_output = f"{speak_output} {user} said \"{item['message']}\"."
        attributes_of(handler_input)[SESSION_LAST_MESSAGE_READ] = item['message']
        logger.info(f"type of last message read: {type(attributes_of(handler_input)[SESSION_LAST_MESSAGE_READ])}")
    return speak_output

class ReadMessageProvideNumberIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input) 
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_NUMBER
            and (
                is_intent_name(PROVIDE_NUMBER_INTENT)(handler_input)
                or is_intent_name(ALL_INTENT)(handler_input)
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
        items = items[len(items) - number:]
        speak_output = compile_items_into_speak_output(items, handler_input)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ReadMessageProvideTimeBoundingIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            SESSION_LAST_REQUEST in attributes_of(handler_input)
            and attributes_of(handler_input)[SESSION_LAST_REQUEST] == LAST_REQUEST_NUMBER
            and SESSION_LAST_HANDLER in attributes_of(handler_input)
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
            speak_output = compile_items_into_speak_output(items, handler_input)
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
