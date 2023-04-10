import datetime

from django.utils import timezone
import requests
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.onboarding import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update, extract_user_message_from_update
from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command

import os


def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)

    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)

    update.message.reply_text(text=text,
                              reply_markup=make_keyboard_for_start_command())


def secret_level(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user_id = extract_user_data_from_update(update)['user_id']
    text = static_text.unlock_secret_room.format(
        user_count=User.objects.count(),
        active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    )

    context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


def gpt_answer(update: Update, context: CallbackContext) -> None:
   message = extract_user_message_from_update(update)['message']
   update.message.reply_text(text='Подождите...')

   headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + os.getenv('OPENAI_API_KEY', ''),
   }

   json_data = {
       'model': 'gpt-3.5-turbo',
       'messages': [
           {
               'role': 'user',
               'content': f'{message}',
           },
       ],
       'temperature': 0.7,
   }
   response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=json_data)
   message_answer = response.json()['choices'][0]['message']['content']
   update.message.reply_text(text=message_answer)