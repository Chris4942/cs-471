import logging
import os
from datetime import date, datetime
from dateutil.parser import isoparse
import boto3
from botocore.exceptions import ClientError
import ask_sdk_core.utils as ask_utils

class ChannelNotFoundException(Exception):
    def __init__(self, message):
        super(ChannelNotFoundException, self)
        self.message = message

from secrets import HEADERS

from requests import get, post

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3',
                             region_name=os.environ.get('S3_PERSISTENCE_REGION'),
                             config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

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
    response_object = get('https://slack.com/api/conversations.list', headers=HEADERS).json()
    logger.info(f"response object from conversations.list: {response_object}")
    channels = response_object['channels']
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


def get_source(name_resolver, channel_resolver, index):
    name, name_confidence = name_resolver(index)
    channel, channel_confidence = channel_resolver(index)
    return name if name_confidence > channel_confidence else channel


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
