import requests
import os

from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.user_prompt.static_text import wait_message, smth_goes_wrong, context_already_deleted, context_deleted
from tgbot.handlers.utils.info import extract_user_message_from_update
from users.models import User, UserPrompt


def delete_context(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    try:
        UserPrompt.objects.filter(user=u).update(user_prompt=[])
        update.message.reply_text(text=context_deleted)
    except UserPrompt.DoesNotExist:
        update.message.reply_text(text=context_already_deleted)

# 123
def gpt_answer(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)

    message = extract_user_message_from_update(update)['message']
    update.message.reply_text(text=wait_message)

    user_prompt_object, create = UserPrompt.objects.get_or_create(user=u)
    user_prompt_object = UserPrompt.objects.filter(user=u).first()


    user_prompt_object.user_prompt.append(
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
    try:
        message_answer = response.json()['choices'][0]['message']['content']
    except KeyError:
        print(response.json())
        message_answer = smth_goes_wrong

    update.message.reply_text(text=message_answer)

    user_prompt_object.user_prompt.append(response.json()['choices'][0]['message'])
    user_prompt_object.save()
    
