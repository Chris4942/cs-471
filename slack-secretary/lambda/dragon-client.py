import requests
import json

URL = 'https://67bb-128-187-83-1.ngrok.io/evie'

class DRAGN_Head_Client: 
    def __init__(self, server_url=URL): 
        self.server_url = server_url 
 
    def run(self, *args): 
        headers = {'Content-type': 'application/json'} 
        data = json.dumps(args) 
        print(data)
        response = requests.post(self.server_url, data=data, headers=headers) 
        return response 
 
 
if __name__ == '__main__': 
    client = DRAGN_Head_Client() 
    result = client.run('dialogpt', 'generate_response', 0, "Q: how can I politely explain that this job is demanding too much of my time. A: ")
    print(result.json())