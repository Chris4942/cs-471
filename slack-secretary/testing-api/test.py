import requests

headers = {"Authorization": "Bearer xoxb-4753428053280-4742434306049-9soWlaebmTXMm2XkZRbfQLJL"}

def get_conversations():
    return requests.get('https://slack.com/api/conversations.list?pretty=1', headers=headers)

def get_list_of_users():
    return requests.get('https://slack.com/api/users.list', headers=headers)

def post_message(message):
    return requests.post("https://slack.com/api/chat.postMessage", data={
        "channel": "U04MFMJ777C",
        "text": message,
    } ,headers=headers)

def get_conversation_list():
    return requests.get('https://slack.com/api/conversations.list', headers=headers)

def get_messages_from(location):
    return requests.get(f"https://slack.com/api/conversations.history?channel={location}", headers=headers)

# print(get_conversations().json())
# print(post_message("test direct message").json())
# print(get_list_of_users().json()["members"])
# print(get_conversation_list().json())
print(get_messages_from('C04MCPDNC1K').json())