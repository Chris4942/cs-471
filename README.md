# Large Language Model Assignment

## DraftMessageIntent
`slack-secretary/lambda/send_message.py` contains a handler called `DraftMessageIntentHandler`. This handler creates a message that is then stored in the same way as other messages. It is included in the output so that the user can hear the message and decide if they want to send it to someone. This meets the requirements of all three uses.
- The response includes both hard-coded text and language model output.
- The prompt uses prompt engineering to coerce the model to speak on a certain subject.
- The handler is capable of handling unexpected input text.

### How to trigger
1. Open slack secretary by saying _"open slack secretary"_.
2. Trigger the intent handler by saying something like _"draft a message saying {prompt}"_
3. Provide the name of the user you would like to send it to
    - Currently, this only supports users, not channels
4. Confirm that you want to send it by saying something like _"yes"_

## DraftQuestionIntent
`slack-secretary/lambda/send_message.py` contains a handler called `DraftQuestionIntentHandler`. This handler functions very similarily to the `DraftMessageIntentHandler`, but it uses a different wrapper to call through to chat gpt. When using the same propmpt, it generated text that was overly polite; for example, whe I asked _"draft a message asking if i can take the rest of the day off"_ it gave the gave the response:
> Here's your message: Dear {Name}, I hope this message finds you well. I am writing to inquire if I may take the rest of the day off. Please let me know what your thoughts are and I will be grateful for any response. Thank you for your time. Sincerely, [Your Name] Who should I send it to?
This is far too polite for slack messages, so to get around that I created another handler with a different prompt that wraps the users request and prefixes it with `"politely but casually"` (see `slack-secretary/lambda/open_ai_client.py` for more details). Adding but casually brought the responses to a much less pretentious level.
- The response includes both hard-coded text and language model output.
- The prompt uses prompt engineering to coerce the model to speak on a certain subject.
- The handler is capable of handling unexpected input text.

### How to trigger
1. Open slack secretary by saying _"open slack secretary"_
2. Trigger the intent handler by saying something like _"draft a message asking {prompt}"_
3. Provide the name of the user you would like to send it to.
    - Currently, this only supports users, not channels
4. Confirm that you want to send it by saying something like _"yes"_

## DraftReplyIntent
`slack-secretary/lambda/send_message.py` contains a handler called
`DraftQuestionIntentHandler`. This handler functions similarily to the other two mentioned, but instead of generating a message to send based on an intend meaning, it generates a response to an already existing message.
- The response includes both hard-coded text and language model output.
- The prompt uses prompt engineering to coerce the model to speak on a certain subject.
- The handler is capable of handling unexpected input text.

### How to trigger
1. Open slack secretary by saying _"open slack secretary"_
2. Have it read you messages by saying _"read messages from {channel, e.g., the busy channel}"_
3. Tell it how many messages you want to hear if prompted
4. Trigger the intent handler by saying something like _"How should I reply?"_
5. Provide the name of the user you would like to send it to.
    - Currently, this only supports users, not channels
    - This should default to responding to the channel that was already referenced, but that functionality is currently not supported
4. Confirm that you want to send it by saying something like _"yes"_

## ProvideLocationIntent
`slack-secretary/lambda/send_message.py` there is an intent for providing a location. This intent will repeat back the message and the destination to the user. It is triggered in all of the above workflows when Alexa says
> This is your message {message} Should I send it?
- The response include both hard-coded text and language model output