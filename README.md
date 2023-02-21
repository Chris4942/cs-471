# Large Language Model Assignment

## DraftMessageIntent
`slack-secretary/lambda/read_message.py` contains a handler called `DraftMessageIntentHandler`. This handler creates a message that is then stored in the same way as other messages. It is included in the output so that the user can hear the message and decide if they want to send it to someone. This meets the requirements of all three uses.
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
`slack-secretary/lambda/read_message.py` contains a handler called `DraftQuestionIntentHandler`. This handler functions very similarily to the `DraftMessageIntentHandler`, but it uses a different wrapper to call through to chat gpt. When using the same propmpt, it generated text that was overly polite; for example, whe I asked _"draft a message asking if i can take the rest of the day off"_ it gave the gave the response:
> Here's your message: Dear {Name}, I hope this message finds you well. I am writing to inquire if I may take the rest of the day off. Please let me know what your thoughts are and I will be grateful for any response. Thank you for your time. Sincerely, [Your Name] Who should I send it to?
This is far too polite for slack messages, so to get around that I created another handler with a different prompt that wraps the users request and prefixes it with `"politely but casually"` (see `slack-secretary/lambda/open_ai_client.py` for more details). Adding but casually brought the responses to a much less pretentious level.

### How to trigger
1. Open slack secretary by saying _"open slack secretary"_
2. Trigger the intent handler by saying something like _"draft a message asking {prompt}"_
3. Provide the name of the user you would like to send it to.
    - Currently, this only supports users, not channels
4. Confirm that you want to send it by saying something like _"yes"_
