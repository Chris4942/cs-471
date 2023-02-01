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

# print(get_conversations().json())
# print(post_message("test direct message").json())
print(get_list_of_users().json()["members"])