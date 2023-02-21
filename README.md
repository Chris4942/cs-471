# Large Language Model Assignment

## DraftMessageIntent
`slack-secretary/lambda/read_message.py` contains a handler called `DraftMessageIntentHandler`. This handler creates a message that is then stored in the same way as other messages. It is included in the output so that the user can hear the message and decide if they want to send it to someone. This meets the requirements of all three uses.
- The response includes both hard-coded text and language model output.
- The prompt uses prompt engineering to coerce the model to speak on a certain subject.
- The handler is capable of handling unexpected input text.

### How to trigger
1. Open slack secretary by saying _"open slack secretary"_.
2. Trigger the intent handler by saying something like _"draft a message saying {prompt}"_
3. Provide the name of the user you would like to send it too.
    - Currently, this only supports users, not channels
4. Confirm that you want to send it by saying something like _"yes"_



