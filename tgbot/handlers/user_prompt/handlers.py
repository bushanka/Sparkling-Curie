import requests
import os

from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.user_prompt.static_text import wait_message
from tgbot.handlers.utils.info import extract_user_message_from_update
from django.core.exceptions import ObjectDoesNotExist
from users.models import User, UserPrompt


def gpt_answer(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)

    message = extract_user_message_from_update(update)['message']
    update.message.reply_text(text=wait_message)

    user_prompt_object, create = UserPrompt.objects.get_or_create(user=u)
    user_prompt_object = UserPrompt.objects.filter(user=u).first()
    print(user_prompt_object.user_prompt)
    print(type(user_prompt_object.user_prompt))
    
    prev_prompt = user_prompt_object.user_prompt
    if prev_prompt is None:
        prev_prompt = []

    user_prompt_object.user_prompt = prev_prompt.append(
          {
          'role': 'user',
          'content': f'{message}'
          }
    )

    user_prompt_object.save()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + os.getenv('OPENAI_API_KEY', ''),
    }

    json_data = {
        'model': 'gpt-3.5-turbo',
        'messages': user_prompt_object.user_prompt,
        'temperature': 0.7,
    }
    
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=json_data)
    message_answer = response.json()['choices'][0]['message']['content']
    update.message.reply_text(text=message_answer)

    prev_prompt = user_prompt_object.user_prompt
    user_prompt_object.user_prompt = prev_prompt.append(response.json()['choices'][0]['message'])
    user_prompt_object.save()
    