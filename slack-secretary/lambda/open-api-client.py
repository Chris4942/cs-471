import openai
import os
import secrets

openai.api_key = secrets.OPEN_AI_API_KEY


def draft_message(prompt: str) -> str:
    gpt3_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Me: Can you draft a message saying that {prompt} in a polite style \nYou:",
        temperature=0.8,
        max_tokens = 100,
    )
    return gpt3_response.choices[0].text
